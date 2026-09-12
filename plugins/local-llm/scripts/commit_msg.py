#!/usr/bin/env python3
"""ステージ済みの変更からコミットメッセージをローカルLLMで生成する。

使い方:
    git add <files>
    python3 commit_msg.py            # メッセージ案を表示
    git commit -m "$(python3 commit_msg.py)"   # そのまま使う
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.STRONG_MODEL)

RULES = """規約:
- 1行目: 変更内容の要約。簡潔かつ平易な表現(主語や冗長な表現は省略)。72文字以内
- 「修正」「調整」「改善」などの曖昧な語を使わず、具体的に何をしたかを書く(例: 「タイムアウトを60秒に変更」)
- feat: や fix: などのプレフィックスは付けない
- 複数の変更を含む場合は、1行目の後に空行を挟み、Markdownの箇条書き(- )で変更ごとに列挙する
- 変更が単一なら1行目のみ(箇条書きにしない)
- diffから読み取れないこと(目的の推測、diffに無いファイル名)は書かない"""

SYSTEM = f"""あなたは git のコミットメッセージを書くアシスタントです。
ユーザーから git diff が渡されます。あなたの仕事は「コミットメッセージを日本語で1つ書く」ことだけです。
コードの解説・修正案・質問への回答はしません。

{RULES}

出力はコミットメッセージ本文のみ。説明・前置き・引用符・コードフェンスは付けない。"""

RESTATE = "上の diff に対するコミットメッセージだけを出力してください(解説やコードは出力しない)。" \
          "複数の変更なら 1行目 + 空行 + 箇条書き、単一なら1行のみ。プレフィックスと「修正」「調整」は禁止。"

SUMMARY_SYSTEM = """あなたは git diff を読んで変更点を列挙するアシスタントです。
渡された diff の断片(全体の一部)について、何をどう変えたかを日本語の箇条書きで簡潔に列挙してください。
ファイル名を添え、diff から読み取れることだけを書く。解説やコードは不要。"""


def summarize_chunk(chunk: str, model: str, idx: int, total: int) -> tuple[str, dict]:
    return oc.chat(
        oc.build_messages(SUMMARY_SYSTEM, f"### diff({idx}/{total})\n```diff\n{chunk}\n```",
                          "この断片の変更点を箇条書きで列挙してください。"),
        model, temperature=0.1, label=f"{model} 要約 {idx}/{total}",
    )


def generate(diff: str, model: str = MODEL) -> tuple[str, dict]:
    """diffからコミットメッセージを生成し (メッセージ, 実行統計) を返す。evals/ からも呼ばれる本体。

    差分が大きい場合はファイル単位のチャンクを先に要約し、要約と変更ファイル一覧から
    メッセージを組み立てる(先頭切り捨てで後半の変更が落ちるのを防ぐ)。
    """
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
            s, st = summarize_chunk(chunk, model, i, len(chunks))
            summaries.append(s)
            stats_list.append(st)
        user = (f"### 変更ファイル\n{stat}\n\n### 変更点の要約(diff を分割して読んだもの)\n"
                + "\n\n".join(summaries))
    if skipped:
        user += f"\n\n(lock ファイル・生成物として除外: {', '.join(skipped[:10])})"

    message, st = oc.chat(oc.build_messages(SYSTEM, user, RESTATE), model, temperature=0.2, label=model)
    stats_list.append(st)
    return clean(message), oc.merge_stats(stats_list)


def clean(message: str) -> str:
    """モデルが付けがちな囲み(コードフェンス・引用符)を外す。"""
    m = message.strip()
    if m.startswith("```"):
        m = m.split("\n", 1)[1] if "\n" in m else ""
        m = m.rsplit("```", 1)[0]
    m = m.strip()
    for a, b in ('""', "''", "``", "「」"):
        if len(m) > 1 and m[0] == a and m[-1] == b:
            m = m[1:-1]
    return m.strip()


def main() -> None:
    diff = subprocess.run(
        ["git", "diff", "--cached", "--no-color"], capture_output=True, text=True, check=True,
    ).stdout
    if not diff.strip():
        sys.exit("ステージ済みの変更がありません (git add してから実行)")
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    message, _ = generate(diff, model)
    print(message)


if __name__ == "__main__":
    main()
