#!/usr/bin/env python3
"""baseブランチとの差分からPR本文をローカルLLMで生成する。

使い方:
    python3 pr_body.py                # git diff HEAD の差分
    python3 pr_body.py origin/main    # 指定refとの差分
    git diff origin/main | python3 pr_body.py -
    gh pr create --title "..." --body "$(python3 pr_body.py origin/main)"
"""

import json
import os
import subprocess
import sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("LOCAL_REVIEW_MODEL", "gemma4:12b")

PROMPT = """次のgit diffから、GitHub PRの本文を日本語のMarkdownで生成してください。

規約:
- ## Summary: 変更内容を箇条書き1〜3点で(diffから読み取れる範囲で、何をどう変えたか)
- ## Test plan: diffから読み取れる確認観点を `- [ ] ` のチェックリストで列挙する
- 「修正」「調整」などの曖昧な表現を避け、具体的に何をしたかを書く
- diffから読み取れないこと(背景・意図の推測、コミットメッセージの丸写し)は書かない
- 出力はPR本文のみ。説明や引用符、コードフェンスは不要

### diff
"""


def get_diff() -> str:
    if len(sys.argv) > 1 and sys.argv[1] == "-":
        return sys.stdin.read()
    base = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    return subprocess.run(
        ["git", "diff", base, "--no-color"],
        capture_output=True, text=True, check=True,
    ).stdout


def main() -> None:
    diff = get_diff()
    if not diff.strip():
        sys.exit("差分がありません")

    # 巨大diffは先頭を優先して切り詰める(コンテキスト保護)
    if len(diff) > 40000:
        diff = diff[:40000] + "\n... (以下省略)"

    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2, "num_ctx": 16384},
        "messages": [{"role": "user", "content": PROMPT + diff}],
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as res:
        print(json.loads(res.read())["message"]["content"].strip())


if __name__ == "__main__":
    main()
