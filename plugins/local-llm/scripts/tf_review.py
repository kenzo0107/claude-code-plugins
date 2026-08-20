#!/usr/bin/env python3
"""Terraformの変更差分をMedPeer規約に照らしてローカルLLMでプレレビューする。

push前のセルフチェック用。クラウドLLMの利用枠を消費せず何度でも実行できる。
指摘はあくまで参考(偽陽性あり得る)。最終判断は人間とCI(fmt/tflint/trivy)が担う。

使い方:
    cd <terraformリポジトリ>
    python3 <このファイル>                  # git diff HEAD の *.tf をレビュー
    python3 <このファイル> origin/main      # 指定refとの差分をレビュー
    git diff main -- '*.tf' | python3 <このファイル> -   # diffを標準入力から
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("TF_REVIEW_MODEL", "gemma4:12b")
RULES_PATH = Path(
    "~/.claude/plugins/marketplaces/cc-sre-plugins/plugins/medpeer-terraform/"
    "skills/medpeer-terraform/SKILL.md"
).expanduser()

PROMPT = """あなたはMedPeerのTerraformコーディング規約のレビュアーです。
以下の「規約」に照らして「差分」をレビューし、規約違反・懸念のみをJSONで返してください。

ルール:
- 差分に現れた変更行(+の行)だけを対象にする。既存コードの問題は指摘しない
- 規約に根拠がある指摘のみ。一般論やスタイルの好みは出さない
- 確信が持てないものは confidence を "low" にする
- 問題がなければ {"findings": []} を返す

出力形式(JSONのみ):
{"findings": [
  {"file": "ファイル名", "rule": "違反した規約の見出し", "issue": "何が問題か(1文)",
   "fix": "修正案(コード断片可)", "confidence": "high|low"}
]}

### 規約
"""


def get_diff() -> str:
    if len(sys.argv) > 1 and sys.argv[1] == "-":
        return sys.stdin.read()
    base = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    return subprocess.run(
        ["git", "diff", base, "--", "*.tf"],
        capture_output=True, text=True, check=True,
    ).stdout


def main() -> None:
    if not RULES_PATH.exists():
        sys.exit(f"規約ファイルが見つかりません: {RULES_PATH}\n"
                 "(medpeer-terraformプラグインの配置が変わった可能性。パスを更新してください)")
    diff = get_diff()
    if not diff.strip():
        print("対象となる .tf の差分がありません")
        return

    rules = RULES_PATH.read_text()
    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_ctx": 16384},
        "messages": [{
            "role": "user",
            "content": f"{PROMPT}{rules}\n\n### 差分\n```diff\n{diff}\n```",
        }],
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as res:
        findings = json.loads(json.loads(res.read())["message"]["content"]).get("findings", [])

    if not findings:
        print("規約違反の指摘はありません(参考: ローカルLLMによるプレレビュー)")
        return
    print(f"指摘 {len(findings)} 件(ローカルLLMのプレレビュー。偽陽性あり得ます):\n")
    for i, f in enumerate(findings, 1):
        mark = "" if f.get("confidence") == "high" else " (低確度)"
        print(f"{i}. [{f.get('file', '?')}] {f.get('rule', '?')}{mark}")
        print(f"   問題: {f.get('issue', '')}")
        print(f"   修正: {f.get('fix', '')}\n")


if __name__ == "__main__":
    main()
