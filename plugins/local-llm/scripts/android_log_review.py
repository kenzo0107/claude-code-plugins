#!/usr/bin/env python3
"""Android/Gradleのビルド・インストール失敗ログを、原因と修正案に絞ってローカルLLMで診断する。

ビルド・インストール自体の実行(決定的な処理)はコマンド側の直接シェル実行が担う。
このスクリプトは「失敗した場合にログを読んで原因を推測する」判断部分だけを
ローカルLLMに任せ、クラウド利用枠を消費しない。

使い方:
    ./gradlew assembleDebug 2>&1 | tee /tmp/android_build.log
    python3 android_log_review.py /tmp/android_build.log
    ./gradlew assembleDebug 2>&1 | python3 android_log_review.py -
"""

import json
import os
import sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("LOCAL_REVIEW_MODEL", "gemma4:12b")

PROMPT = """あなたはAndroid/Gradleビルドのトラブルシューティングに詳しいエンジニアです。
以下の「ビルドログ」から失敗の原因を特定し、JSONで返してください。

ルール:
- ログに実際に現れたエラー・スタックトレースのみを根拠にする(推測での深読みはしない)
- 原因が複数考えられる場合は最も可能性が高いものを1つ挙げる
- 確信が持てない場合は confidence を "low" にする
- ビルドが失敗していない(成功ログ)場合は {"cause": null} を返す

出力形式(JSONのみ):
{"cause": "根本原因(1-2文)", "fix": "修正手順(具体的なコマンドや変更点)",
 "confidence": "high|low"}

### ビルドログ
"""


def get_log() -> str:
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
            return f.read()
    return sys.stdin.read()


def main() -> None:
    log = get_log()
    if not log.strip():
        sys.exit("ログが空です")

    # 巨大ログはエラーが集中する末尾を優先して切り詰める(コンテキスト保護)
    if len(log) > 40000:
        log = "... (前略)\n" + log[-40000:]

    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_ctx": 16384},
        "messages": [{"role": "user", "content": PROMPT + log}],
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as res:
        result = json.loads(json.loads(res.read())["message"]["content"])

    if not result.get("cause"):
        print(f"失敗の原因を特定できませんでした(ローカルLLM={MODEL})。ログを人手で確認してください")
        return
    mark = "" if result.get("confidence") == "high" else " (低確度)"
    print(f"原因{mark}: {result['cause']}")
    print(f"修正案: {result.get('fix', '')}")


if __name__ == "__main__":
    main()
