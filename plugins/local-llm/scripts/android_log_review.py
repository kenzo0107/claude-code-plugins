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

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL)
MAX_LOG_CHARS = 40000

SYSTEM = """あなたはAndroid/Gradleビルドのトラブルシューティングに詳しいエンジニアです。
ユーザーからビルドログが渡されます。失敗の根本原因を特定し、JSON で返してください。

ルール:
- ログに実際に現れたエラー・スタックトレースのみを根拠にする(推測での深読みはしない)
- 原因が複数考えられる場合は最も可能性が高いものを1つ挙げる
- 確信が持てない場合は confidence を "low" にする
- ビルドが失敗していない(成功ログ)場合は cause を null にする"""

RESTATE = """出力は JSON のみ:
{"cause": "根本原因(1-2文)または null", "evidence": "根拠となるログ行を1行そのまま", "fix": "修正手順(具体的なコマンドや変更点)", "confidence": "high|low"}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "cause": {"type": ["string", "null"]},
        "evidence": {"type": "string"},
        "fix": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "low"]},
    },
    "required": ["cause", "evidence", "fix", "confidence"],
}

ERROR_RE = re.compile(r"(?i)\b(error|exception|failed|FAILURE|What went wrong|INSTALL_FAILED)\b")


def get_log() -> str:
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
            return f.read()
    return sys.stdin.read()


def focus(log: str) -> str:
    """巨大ログはエラー行の周辺と末尾を優先して残す。"""
    if len(log) <= MAX_LOG_CHARS:
        return log
    lines = log.splitlines()
    keep = set()
    for i, l in enumerate(lines):
        if ERROR_RE.search(l):
            keep.update(range(max(0, i - 3), min(len(lines), i + 15)))
    keep.update(range(max(0, len(lines) - 80), len(lines)))
    picked, last = [], -1
    for i in sorted(keep):
        if i != last + 1:
            picked.append("... (中略)")
        picked.append(lines[i])
        last = i
    text = "\n".join(picked)
    return text[-MAX_LOG_CHARS:] if len(text) > MAX_LOG_CHARS else text


def diagnose(log: str, model: str = MODEL) -> tuple[dict, dict]:
    user = f"### ビルドログ\n```\n{focus(log)}\n```"
    return oc.chat_json(oc.build_messages(SYSTEM, user, RESTATE), model, SCHEMA, temperature=0.1, label=model)


def main() -> None:
    log = get_log()
    if not log.strip():
        sys.exit("ログが空です")
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    result, _ = diagnose(log, model)
    if not result.get("cause"):
        print(f"失敗の原因を特定できませんでした(ローカルLLM={model})。ログを人手で確認してください")
        return
    mark = "" if result.get("confidence") == "high" else " (低確度)"
    print(f"原因{mark}: {result['cause']}")
    if result.get("evidence"):
        print(f"根拠: {result['evidence'].strip()}")
    print(f"修正案: {result.get('fix', '')}")


if __name__ == "__main__":
    main()
