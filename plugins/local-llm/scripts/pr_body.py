#!/usr/bin/env python3
"""baseブランチとの差分からPR本文をローカルLLMで生成する。

使い方:
    python3 pr_body.py                # git diff HEAD の差分
    python3 pr_body.py origin/main    # 指定refとの差分
    git diff origin/main | python3 pr_body.py -
    gh pr create --title "..." --body "$(python3 pr_body.py origin/main)"
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import commit_msg  # noqa: E402
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL)

SYSTEM = """あなたは GitHub の Pull Request 本文を書くアシスタントです。
ユーザーから git diff(または diff の要約)が渡されます。あなたの仕事は「PR本文を日本語の Markdown で書く」ことだけです。
コードの解説・修正案は書きません。

規約:
- `## Summary`: 変更内容を箇条書き1〜5点で(diff から読み取れる範囲で、何をどう変えたか)
- `## Test plan`: diff から読み取れる確認観点を `- [ ] ` のチェックリストで列挙する
- 「修正」「調整」「改善」などの曖昧な語を使わず、具体的に何をしたかを書く
- diff から読み取れないこと(背景・意図の推測、diff に無いファイル名)は書かない
- 出力は PR 本文のみ。説明・前置き・コードフェンスは不要"""

RESTATE = "上の内容に対する PR 本文(## Summary と ## Test plan の2節)だけを Markdown で出力してください。"


def get_diff() -> str:
    if len(sys.argv) > 1 and sys.argv[1] == "-":
        return sys.stdin.read()
    base = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    return subprocess.run(["git", "diff", base, "--no-color"], capture_output=True, text=True, check=True).stdout


def generate(diff: str, model: str = MODEL) -> tuple[str, dict]:
    """diff から PR 本文を生成し (本文, 実行統計) を返す。大きな diff は分割要約してから書く。"""
    chunks, stat, skipped = oc.prepare_diff(diff)
    if not chunks:
        chunks, stat = [diff], ""
    stats_list = []
    if len(chunks) == 1:
        user = f"### 変更ファイル\n{stat}\n\n### diff\n```diff\n{chunks[0]}\n```"
    else:
        oc.log(f"[local-llm] 差分が大きいため {len(chunks)} 分割で要約してから生成します")
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            s, st = commit_msg.summarize_chunk(chunk, model, i, len(chunks))
            summaries.append(s)
            stats_list.append(st)
        user = f"### 変更ファイル\n{stat}\n\n### 変更点の要約(diff を分割して読んだもの)\n" + "\n\n".join(summaries)
    if skipped:
        user += f"\n\n(lock ファイル・生成物として除外: {', '.join(skipped[:10])})"
    body, st = oc.chat(oc.build_messages(SYSTEM, user, RESTATE), model, temperature=0.2, label=model)
    stats_list.append(st)
    return commit_msg.clean(body), oc.merge_stats(stats_list)


def main() -> None:
    diff = get_diff()
    if not diff.strip():
        sys.exit("差分がありません")
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    body, _ = generate(diff, model)
    print(body)


if __name__ == "__main__":
    main()
