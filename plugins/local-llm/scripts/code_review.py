#!/usr/bin/env python3
"""コード差分を観点ファイル(ルール)に照らしてローカルLLMでプレレビューする汎用版。

tf_review.py の汎用化。観点ファイルを差し替えれば任意の言語・観点に使える。
指摘は参考情報(偽陽性あり得る)。決定的なツール(linter, gosec等)の代替ではない。

使い方:
    python3 code_review.py rules/go-security.md              # git diff HEAD の差分
    python3 code_review.py rules/go-security.md origin/main  # 指定refとの差分
    git diff main | python3 code_review.py rules/go-security.md -
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("LOCAL_REVIEW_MODEL", "gemma4:12b")

PROMPT = """あなたは経験豊富なコードレビュアーです。
以下の「レビュー観点」に照らして「差分」をレビューし、該当する問題のみをJSONで返してください。

ルール:
- 差分に現れた変更行(+の行)だけを対象にする
- 観点に根拠がある指摘のみ。一般論やスタイルの好みは出さない
- 確信が持てないもの(外部入力が届くか不明など)は confidence を "low" にする
- 問題がなければ {"findings": []} を返す

出力形式(JSONのみ):
{"findings": [
  {"file": "ファイル名", "category": "観点の見出し", "issue": "何が問題か(1-2文)",
   "fix": "修正案(コード断片可)", "confidence": "high|low"}
]}

### レビュー観点
"""


def get_diff() -> str:
    if len(sys.argv) > 2 and sys.argv[2] == "-":
        return sys.stdin.read()
    base = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    return subprocess.run(
        ["git", "diff", base],
        capture_output=True, text=True, check=True,
    ).stdout


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: code_review.py <rules.md> [base|-]")
    rules_path = Path(sys.argv[1])
    if not rules_path.exists():
        sys.exit(f"観点ファイルが見つかりません: {rules_path}")

    diff = get_diff()
    if not diff.strip():
        print("差分がありません")
        return

    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_ctx": 16384},
        "messages": [{
            "role": "user",
            "content": f"{PROMPT}{rules_path.read_text()}\n\n### 差分\n```diff\n{diff}\n```",
        }],
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=900) as res:
        findings = json.loads(json.loads(res.read())["message"]["content"]).get("findings", [])

    if not findings:
        print(f"指摘なし(ローカルLLM={MODEL} によるプレレビュー)")
        return
    print(f"指摘 {len(findings)} 件(ローカルLLM={MODEL}。偽陽性あり得ます):\n")
    for i, f in enumerate(findings, 1):
        mark = "" if f.get("confidence") == "high" else " (低確度)"
        print(f"{i}. [{f.get('file', '?')}] {f.get('category', '?')}{mark}")
        print(f"   問題: {f.get('issue', '')}")
        print(f"   修正: {f.get('fix', '')}\n")


if __name__ == "__main__":
    main()
