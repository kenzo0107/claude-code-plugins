#!/usr/bin/env python3
"""ログ・テキスト中の個人情報をローカルLLM+正規表現でマスキングする。

クラウドLLMにログを渡す前の前処理として使う(雑誌SD 2026/9 第3章の方式の堅牢版)。

設計:
  1. 正規表現で確実に検出できるもの(メール・IP・電話番号)を機械的に置換
  2. 人名など文脈依存のPIIはローカルLLMに「列挙だけ」させ、置換はコードで行う
     (LLMに全文を書き換えさせない = ログ本体の改変事故を防ぐ)
  3. 最後に正規表現で再走査し、マスク漏れがあれば警告(exit 2)
  4. 復元用の変換表を <出力>.map.json に保存(変換表自体がPIIなので外に出さないこと)

使い方:
  python3 anonymize.py input.log                # → input.masked.log と input.masked.log.map.json
  cat input.log | python3 anonymize.py -        # → stdout(変換表は stderr に出力)
"""

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL)

# 1段目: 決定的に検出できるパターン
PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "IP": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "PHONE": re.compile(r"\b0\d{1,4}-\d{1,4}-\d{3,4}\b"),
}

SYSTEM = """あなたはログから個人情報(PII)を抽出する検出器です。ユーザーからシステムのログが渡されます。
その中に残っている個人情報を列挙してください。書き換えはせず、列挙だけを行います。

対象: 人名(氏名・姓・名)、住所、生年月日、その他個人を特定できる文字列
対象外: すでに [EMAIL_1] のような形式でマスク済みのもの、システム名・テーブル名・カラム名・SQL予約語・変数名"""

RESTATE = """出力は JSON のみ: {"pii": [{"value": "テキスト中の完全一致文字列", "type": "NAME|ADDRESS|BIRTHDAY|OTHER"}]}
個人情報がなければ {"pii": []}。value はテキストに現れる文字列と完全一致させること。"""

SCHEMA = {
    "type": "object",
    "properties": {
        "pii": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "type": {"type": "string", "enum": ["NAME", "ADDRESS", "BIRTHDAY", "OTHER"]},
                },
                "required": ["value", "type"],
            },
        }
    },
    "required": ["pii"],
}

# 長いログはこの文字数ごとに分けて検出する(見落とし防止)
CHUNK_CHARS = 12000


def llm_find_pii(text: str, model: str = MODEL) -> list[dict]:
    found: list[dict] = []
    chunks = [text[i:i + CHUNK_CHARS] for i in range(0, len(text), CHUNK_CHARS)] or [text]
    for i, chunk in enumerate(chunks, 1):
        label = f"{model} {i}/{len(chunks)}" if len(chunks) > 1 else model
        result, _ = oc.chat_json(
            oc.build_messages(SYSTEM, f"### テキスト\n{chunk}", RESTATE), model, SCHEMA,
            temperature=0.0, label=label,
        )
        found.extend(result.get("pii", []))
    return found


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: anonymize.py <input.log | ->")

    src = sys.stdin.read() if sys.argv[1] == "-" else Path(sys.argv[1]).read_text()
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}

    def token_for(kind: str, value: str) -> str:
        for t, v in mapping.items():
            if v == value:
                return t
        counters[kind] = counters.get(kind, 0) + 1
        token = f"[{kind}_{counters[kind]}]"
        mapping[token] = value
        return token

    # 1. 正規表現で機械的にマスク
    masked = src
    for kind, pat in PATTERNS.items():
        masked = pat.sub(lambda m, k=kind: token_for(k, m.group()), masked)

    # 2. LLMで文脈依存PIIを列挙させ、コード側で完全一致置換
    for item in llm_find_pii(masked, model):
        value = item.get("value", "")
        if len(value) >= 2 and value in masked and not re.fullmatch(r"\[[A-Z_0-9]+\]", value):
            masked = masked.replace(value, token_for(item.get("type", "OTHER"), value))

    # 3. マスク漏れの再走査(機械検証)
    leaks = [m.group() for pat in PATTERNS.values() for m in pat.finditer(masked)]

    # 4. 出力
    if sys.argv[1] == "-":
        print(masked)
        print(json.dumps(mapping, ensure_ascii=False), file=sys.stderr)
    else:
        out = Path(sys.argv[1]).with_suffix(".masked" + Path(sys.argv[1]).suffix)
        out.write_text(masked)
        Path(str(out) + ".map.json").write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2) + "\n"
        )
        print(f"masked : {out}")
        print(f"mapping: {out}.map.json (PIIを含む。外部に出さないこと)")
        print(f"replaced: {len(mapping)} 件")

    if leaks:
        print(f"警告: マスク漏れの可能性 {len(leaks)} 件: {leaks}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
