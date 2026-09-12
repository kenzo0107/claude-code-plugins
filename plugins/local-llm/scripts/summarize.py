#!/usr/bin/env python3
"""長いテキスト(ログ・CI出力・diff・ドキュメント)をローカルLLMで要約・説明する汎用ツール。

判断を伴わない「読んで要点を抜き出す」作業をクラウドから逃がすためのもの。
入力の種類はヒューリスティックで自動判定し(--mode で固定可)、長い入力は分割して要約→統合する。

使い方:
    python3 summarize.py build.log                    # ファイルを要約
    ./gradlew test 2>&1 | python3 summarize.py -      # 標準入力
    git diff origin/main | python3 summarize.py - --mode diff
    python3 summarize.py app.log --question "500エラーの原因は何か"
    python3 summarize.py notes.md --lines 5           # 箇条書きの本数
"""

import argparse
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL)

MODES = {
    "log": "アプリケーションやシステムのログ。エラー・警告・異常なパターンを時系列で拾い、正常な繰り返しは省く",
    "ci": "CI/ビルド/テストの出力。失敗したステップ・テスト名・エラーメッセージを優先し、成功したものは件数だけ",
    "diff": "git diff。ファイルごとに何をどう変えたかを列挙する。コードの善し悪しは評価しない",
    "text": "ドキュメントや議事録などの文章。主張・決定事項・TODO を落とさずに要点を抜き出す",
}

SYSTEM_TMPL = """あなたは技術文書の要約者です。ユーザーから長いテキストが渡されます。
入力の種類: {kind}

ルール:
- 入力に書かれていることだけを書く。推測・補足・一般論は加えない
- 固有名詞・ファイル名・エラーメッセージ・数値はそのまま残す(要約で潰さない)
- 日本語で、Markdown の箇条書きで出力する。前置きや締めの文は不要
- 箇条書きは最大 {lines} 本。重要度の高いものから並べる
{question}"""

RESTATE_TMPL = "上のテキストの要点を日本語の箇条書き(最大 {lines} 本)で出力してください。入力に無いことは書かない。{question}"

MERGE_SYSTEM = """あなたは技術文書の要約者です。長いテキストを分割して作った部分要約が渡されます。
重複を統合し、全体として重要な順に並べ直した最終要約を日本語の Markdown 箇条書きで出力してください。
部分要約に無いことは書かない。前置きは不要。"""


def detect_mode(text: str) -> str:
    head = text[:4000]
    if re.search(r"(?m)^diff --git |^@@ -\d+", head):
        return "diff"
    if re.search(r"(?i)\b(BUILD (SUCCESSFUL|FAILED)|Tests? run:|passed|failed|FAIL:|PASS:|npm ERR!|error\[E\d+\]|Task :)", head):
        return "ci"
    if re.search(r"(?m)^\S*\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\b(INFO|WARN|ERROR|DEBUG)\b", head):
        return "log"
    return "text"


def chunk_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    lines = text.splitlines(keepends=True)
    chunks, cur, size = [], [], 0
    for l in lines:
        if size + len(l) > max_chars and cur:
            chunks.append("".join(cur))
            cur, size = [], 0
        cur.append(l)
        size += len(l)
    if cur:
        chunks.append("".join(cur))
    return chunks


def summarize(text: str, mode: str, lines: int, question: str | None, model: str) -> tuple[str, dict]:
    q_sys = f"- ユーザーの質問「{question}」に答えることを最優先にする" if question else ""
    q_re = f"特に「{question}」に答えること。" if question else ""
    system = SYSTEM_TMPL.format(kind=MODES[mode], lines=lines, question=q_sys)
    restate = RESTATE_TMPL.format(lines=lines, question=q_re)
    if mode == "diff":
        chunks, _, _ = oc.prepare_diff(text)
        chunks = chunks or [text]
    else:
        chunks = chunk_text(text, oc.MAX_CHUNK_CHARS)
    stats = []
    if len(chunks) == 1:
        out, st = oc.chat(oc.build_messages(system, f"### 入力\n```\n{chunks[0]}\n```", restate), model, temperature=0.1, label=model)
        return out, st
    oc.log(f"[local-llm] 入力が大きいため {len(chunks)} 分割で要約します")
    partials = []
    for i, c in enumerate(chunks, 1):
        p, st = oc.chat(oc.build_messages(system, f"### 入力({i}/{len(chunks)})\n```\n{c}\n```", restate),
                        model, temperature=0.1, label=f"{model} {i}/{len(chunks)}")
        partials.append(f"#### 部分 {i}\n{p}")
        stats.append(st)
    merged, st = oc.chat(
        oc.build_messages(MERGE_SYSTEM, "\n\n".join(partials),
                          f"統合した最終要約を箇条書き(最大 {lines} 本)で出力。{q_re}"),
        model, temperature=0.1, label=f"{model} 統合",
    )
    stats.append(st)
    return merged, oc.merge_stats(stats)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="ファイルパス、または - で標準入力")
    ap.add_argument("--mode", choices=["auto", *MODES], default="auto")
    ap.add_argument("--lines", type=int, default=8, help="箇条書きの最大本数")
    ap.add_argument("--question", "-q", help="答えてほしい質問(要約の焦点)")
    args = ap.parse_args()

    text = sys.stdin.read() if args.src == "-" else Path(args.src).read_text(errors="replace")
    if not text.strip():
        sys.exit("入力が空です")
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    mode = detect_mode(text) if args.mode == "auto" else args.mode
    oc.log(f"[local-llm] mode={mode} model={model} {len(text)} chars")
    out, _ = summarize(text, mode, args.lines, args.question, model)
    print(out)


if __name__ == "__main__":
    main()
