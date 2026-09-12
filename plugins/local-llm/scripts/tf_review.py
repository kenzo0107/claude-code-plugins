#!/usr/bin/env python3
"""Terraformの変更差分をMedPeer規約に照らしてローカルLLMでプレレビューする。

push前のセルフチェック用。クラウドLLMの利用枠を消費せず何度でも実行できる。
指摘はあくまで参考(偽陽性あり得る)。最終判断は人間とCI(fmt/tflint/trivy)が担う。
レビュー本体は code_review.review を使い、規約ファイルだけを差し替えている。

使い方:
    cd <terraformリポジトリ>
    python3 <このファイル>                  # git diff HEAD の *.tf をレビュー
    python3 <このファイル> origin/main      # 指定refとの差分をレビュー
    git diff main -- '*.tf' | python3 <このファイル> -   # diffを標準入力から
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common"), str(HERE.parent / "code-review")]
import code_review  # noqa: E402
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("TF_REVIEW_MODEL", os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL))
RULES_PATH = Path(os.environ.get(
    "TF_REVIEW_RULES",
    "~/.claude/plugins/marketplaces/cc-sre-plugins/plugins/medpeer-terraform/skills/medpeer-terraform/SKILL.md",
)).expanduser()
TF_EXTS = (".tf", ".tfvars")


def load_rules() -> str:
    if not RULES_PATH.exists():
        sys.exit(f"規約ファイルが見つかりません: {RULES_PATH}\n"
                 "(medpeer-terraformプラグインの配置が変わった可能性。TF_REVIEW_RULES で指定してください)")
    return RULES_PATH.read_text()


def get_diff() -> str:
    if len(sys.argv) > 1 and sys.argv[1] == "-":
        return sys.stdin.read()
    base = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    return subprocess.run(
        ["git", "diff", base, "--no-color", "--", "*.tf", "*.tfvars"],
        capture_output=True, text=True, check=True,
    ).stdout


def review(diff: str, model: str = MODEL) -> tuple[list[dict], dict]:
    return code_review.review(diff, load_rules(), model, TF_EXTS)


def main() -> None:
    diff = get_diff()
    if not diff.strip():
        print("対象となる .tf の差分がありません")
        return
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    findings, _ = review(diff, model)
    if not findings:
        print(f"規約違反の指摘はありません(参考: ローカルLLM={model} によるプレレビュー)")
        return
    print(code_review.format_findings(findings, model).replace("指摘 ", "規約に関する指摘 ", 1))


if __name__ == "__main__":
    main()
