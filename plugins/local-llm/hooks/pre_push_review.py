#!/usr/bin/env python3
"""PreToolUse フック: Claude Code が `git push` を実行する直前に、push 対象の差分をローカルLLMで
プレレビューする。.tf は MedPeer 規約、.go/.py/.rb/.kt/.ts 等は言語別セキュリティ観点。

判断方針:
  - high confidence の指摘あり → permissionDecision "ask"(ユーザーに指摘を見せて承認を求める)
  - low のみ / 指摘なし         → allow(指摘は systemMessage で Claude に渡す)
  - Ollama 未起動・対象差分なし・非 push コマンド → 何もしない(exit 0)
  - 同じ HEAD に対する再実行はキャッシュを返す(承認後の再 push で待たせない)

無効化: 環境変数 LOCAL_LLM_SKIP_PUSH_REVIEW=1
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# リポジトリ: tools/hooks/ から tools/common, tools/code-review, tools/tf-review を参照。プラグイン: hooks/ から scripts/ を参照
sys.path[:0] = [str(HERE), str(HERE.parent / "scripts"), str(HERE.parent / "common"),
                str(HERE.parent / "code-review"), str(HERE.parent / "tf-review")]
import code_review  # noqa: E402
import ollama_client as oc  # noqa: E402

PUSH_RE = re.compile(r"(?<![\w-])git\s+(?:-C\s+\S+\s+)?push\b")
CACHE_DIR = Path(tempfile.gettempdir()) / "local-llm-push-review"
MAX_DIFF_CHARS = 120_000  # これ以上は時間がかかりすぎるためフックでは見ない


def git(cwd: str, *args: str) -> str | None:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def push_base(cwd: str) -> str | None:
    """push で送られる範囲の基点。upstream があればそれ、無ければ origin のデフォルトブランチ。"""
    up = git(cwd, "rev-parse", "--abbrev-ref", "@{upstream}")
    if up:
        return up
    head_ref = git(cwd, "symbolic-ref", "refs/remotes/origin/HEAD")
    if head_ref:
        return head_ref.replace("refs/remotes/", "")
    for cand in ("origin/main", "origin/master", "origin/develop"):
        if git(cwd, "rev-parse", "--verify", "--quiet", cand) is not None:
            return cand
    return None


def emit(decision: str | None, reason: str, system_message: str = "") -> None:
    out: dict = {}
    if decision:
        out["hookSpecificOutput"] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    if system_message:
        out["systemMessage"] = system_message
    if out:
        print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


def run_reviews(diff: str, model: str) -> list[dict]:
    findings: list[dict] = []
    for rule, exts in code_review.rules_for_diff(diff).items():
        f, _ = code_review.review(diff, (code_review.RULES_DIR / rule).read_text(), model, exts)
        findings.extend(f)
    if any(p.path.endswith((".tf", ".tfvars")) for p in oc.split_diff(diff)):
        try:
            import tf_review  # noqa: E402
            if tf_review.RULES_PATH.exists():
                f, _ = code_review.review(diff, tf_review.RULES_PATH.read_text(), model, tf_review.TF_EXTS)
                findings.extend(f)
        except ImportError:
            pass
    return code_review.dedupe(findings)


def main() -> None:
    if os.environ.get("LOCAL_LLM_SKIP_PUSH_REVIEW") == "1":
        return
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    if payload.get("tool_name") != "Bash":
        return
    cmd = (payload.get("tool_input") or {}).get("command", "")
    if not PUSH_RE.search(cmd) or "--dry-run" in cmd:
        return
    cwd = payload.get("cwd") or os.getcwd()
    if git(cwd, "rev-parse", "--is-inside-work-tree") != "true":
        return
    head = git(cwd, "rev-parse", "HEAD")
    base = push_base(cwd)
    if not head or not base:
        return
    diff = git(cwd, "diff", f"{base}...HEAD", "--no-color") or ""
    if not diff.strip() or len(diff) > MAX_DIFF_CHARS:
        return
    if not code_review.rules_for_diff(diff) and not any(p.path.endswith((".tf", ".tfvars")) for p in oc.split_diff(diff)):
        return

    CACHE_DIR.mkdir(exist_ok=True)
    key = hashlib.sha1(f"{cwd}\n{base}\n{head}\n{diff}".encode()).hexdigest()
    cache = CACHE_DIR / f"{key}.json"
    if cache.exists():
        findings = json.loads(cache.read_text())
        model = "cache"
    else:
        try:
            model = oc.resolve_model(os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL), oc.DEFAULT_MODEL)
        except oc.OllamaError:
            return
        oc.QUIET = True
        try:
            findings = run_reviews(diff, model)
        except Exception as e:  # フックは本来の作業を止めない
            emit(None, "", f"[local-llm push プレレビュー] 実行に失敗したためスキップ: {e}")
        cache.write_text(json.dumps(findings, ensure_ascii=False))

    if not findings:
        emit(None, "", f"[local-llm push プレレビュー] {base}...HEAD に指摘なし(model={model})")
    text = code_review.format_findings(findings, model)
    high = [f for f in findings if f.get("confidence") == "high"]
    if high:
        emit("ask",
             f"ローカルLLMのプレレビューで high confidence の指摘が {len(high)} 件あります。内容を確認して push を続けるか判断してください。\n\n{text}",
             f"[local-llm push プレレビュー] 以下の指摘があります。ユーザーが push を承認した場合でも、妥当と判断した指摘はユーザーに伝えること。\n\n{text}")
    emit(None, "", f"[local-llm push プレレビュー] 低確度の指摘のみ(参考):\n\n{text}")


if __name__ == "__main__":
    main()
