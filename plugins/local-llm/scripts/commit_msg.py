#!/usr/bin/env python3
"""ステージ済みの変更からコミットメッセージをローカルLLMで生成する。

使い方:
    git add <files>
    python3 commit_msg.py            # メッセージ案を表示
    git commit -m "$(python3 commit_msg.py)"   # そのまま使う
"""

import json
import os
import subprocess
import sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("LOCAL_REVIEW_MODEL", "gemma4:12b")

PROMPT = """次のgit diff(ステージ済みの変更)から、コミットメッセージを日本語で生成してください。

規約:
- 1行目: 変更内容の要約。簡潔かつ平易な表現(主語や冗長な表現は省略)
- 「修正」「調整」などの曖昧な表現を避け、具体的に何をしたかを書く
- feat: や fix: などのプレフィックスは付けない
- 複数の変更を含む場合は、1行目の後に空行を挟み、Markdownの箇条書きで列挙する
- 変更が単一なら1行目のみでよい
- diffから読み取れないこと(目的の推測など)は書かない

出力はコミットメッセージ本文のみ。説明や引用符は不要。

### diff
"""


def main() -> None:
    diff = subprocess.run(
        ["git", "diff", "--cached", "--no-color"],
        capture_output=True, text=True, check=True,
    ).stdout
    if not diff.strip():
        sys.exit("ステージ済みの変更がありません (git add してから実行)")

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
