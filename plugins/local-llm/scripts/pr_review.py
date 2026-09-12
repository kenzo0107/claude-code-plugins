#!/usr/bin/env python3
"""他人の Pull Request をローカルLLMでプレレビューし、レビューコメント案を Markdown で出す。

`gh pr diff` を入力に、拡張子ごとの観点ファイル(セキュリティ)と一般品質観点で差分をレビューする。
投稿はしない(出力を人が確認してから `gh pr review` / `gh pr comment` で投稿する)。

使い方:
    python3 pr_review.py 123                       # カレントリポジトリの PR #123
    python3 pr_review.py https://github.com/o/r/pull/123
    python3 pr_review.py 123 --repo owner/repo
    python3 pr_review.py 123 --json                # 機械処理用(findings の JSON)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common"), str(HERE.parent / "code-review")]
import code_review  # noqa: E402
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL)
GENERAL_RULES = code_review.RULES_DIR / "general-quality.md"
# 一般品質観点を適用するファイル(言語別観点があるものにはセキュリティ観点と併用)
GENERAL_EXTS = (".go", ".py", ".rb", ".kt", ".kts", ".ts", ".tsx", ".js", ".jsx", ".sh", ".sql", ".tf",
                ".yml", ".yaml", ".java", ".swift", ".rs", ".php", ".cs")


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def fetch_pr(ref: str, repo: str | None) -> tuple[dict, str]:
    repo_args = ["--repo", repo] if repo else []
    meta = json.loads(gh("pr", "view", ref, *repo_args, "--json", "number,title,body,baseRefName,headRefName,url,additions,deletions"))
    diff = gh("pr", "diff", ref, *repo_args)
    return meta, diff


def review_pr(diff: str, model: str) -> tuple[list[dict], list[str]]:
    """言語別セキュリティ観点 + 一般品質観点でレビューし (findings, 使った観点) を返す。"""
    findings: list[dict] = []
    used: list[str] = []
    for rule, exts in code_review.rules_for_diff(diff).items():
        oc.log(f"[local-llm] {rule} で {'/'.join(exts)} をレビュー")
        f, _ = code_review.review(diff, (code_review.RULES_DIR / rule).read_text(), model, exts)
        findings.extend(f)
        used.append(rule)
    if GENERAL_RULES.exists():
        oc.log("[local-llm] general-quality.md で一般品質をレビュー")
        f, _ = code_review.review(diff, GENERAL_RULES.read_text(), model, GENERAL_EXTS)
        findings.extend(f)
        used.append(GENERAL_RULES.name)
    return code_review.dedupe(findings), used


def to_markdown(meta: dict, findings: list[dict], used: list[str], model: str, skipped: list[str]) -> str:
    out = [f"## ローカルLLM プレレビュー: #{meta['number']} {meta['title']}",
           f"モデル: `{model}` / 観点: {', '.join(used) or 'なし'} / 変更: +{meta.get('additions', '?')} -{meta.get('deletions', '?')}",
           ""]
    if skipped:
        out.append(f"対象外として除外: {len(skipped)} ファイル(lock・生成物・バイナリ等)\n")
    if not findings:
        out.append("指摘なし。")
        return "\n".join(out)
    high = [f for f in findings if f.get("confidence") == "high"]
    low = [f for f in findings if f.get("confidence") != "high"]
    for title, items in (("### 要確認(high)", high), ("### 参考(low: 偽陽性の可能性あり)", low)):
        if not items:
            continue
        out.append(title)
        by_file: dict[str, list[dict]] = {}
        for f in items:
            by_file.setdefault(f.get("file", "?"), []).append(f)
        for path, fs in by_file.items():
            out.append(f"\n**{path}**")
            for f in fs:
                out.append(f"- [{f.get('category', '?')}] {f.get('issue', '')}")
                if f.get("snippet"):
                    out.append(f"  - 該当: `{f['snippet'].strip()[:120]}`")
                if f.get("fix"):
                    out.append(f"  - 提案: {f['fix']}")
        out.append("")
    out.append("_ローカルLLMによるプレレビューです。投稿前に人が内容を確認してください。_")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pr", help="PR 番号または URL")
    ap.add_argument("--repo", help="owner/repo(カレントがそのリポジトリでない場合)")
    ap.add_argument("--json", action="store_true", help="findings を JSON で出力")
    args = ap.parse_args()

    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    try:
        meta, diff = fetch_pr(args.pr, args.repo)
    except subprocess.CalledProcessError as e:
        sys.exit(f"gh の実行に失敗しました: {e.stderr.strip()}")
    if not diff.strip():
        sys.exit("PR に差分がありません")

    _, _, skipped = oc.prepare_diff(diff)
    findings, used = review_pr(diff, model)
    if args.json:
        print(json.dumps({"pr": meta, "model": model, "rules": used, "findings": findings}, ensure_ascii=False, indent=2))
        return
    print(to_markdown(meta, findings, used, model, skipped))


if __name__ == "__main__":
    main()
