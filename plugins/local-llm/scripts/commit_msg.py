#!/usr/bin/env python3
"""ステージ済みの変更からコミットメッセージをローカルLLMで生成する。

使い方:
    git add <files>
    python3 commit_msg.py            # メッセージ案を表示
    git commit -m "$(python3 commit_msg.py)"   # そのまま使う
"""

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.STRONG_MODEL)

# 行内差分(語単位。和文は区切りが無いので1文字単位)。文章のように1行が長いファイルで、
# 一語の変更が段落まるごとの -/+ 2行になって入力が膨らむのを防ぐ
WORD_DIFF_ARGS = ["-U0", "--word-diff=plain", "--word-diff-regex=[A-Za-z0-9_]+|[^[:space:]]"]
# 行内差分で変更箇所の前後に残す未変更文字数
WORD_DIFF_KEEP = int(os.environ.get("LOCAL_LLM_WORD_DIFF_KEEP", "30"))

RULES = """規約:
- 1行目: 変更内容の要約。簡潔かつ平易な表現(主語や冗長な表現は省略)。72文字以内
- 「修正」「調整」「改善」などの曖昧な語を使わず、具体的に何をしたかを書く(例: 「タイムアウトを60秒に変更」)
- feat: や fix: などのプレフィックスは付けない
- 複数の変更を含む場合は、1行目の後に空行を挟み、Markdownの箇条書き(- )で変更ごとに列挙する
- 変更が単一なら1行目のみ(箇条書きにしない)
- diffから読み取れないこと(目的の推測、diffに無いファイル名)は書かない"""

SYSTEM = f"""あなたは git のコミットメッセージを書くアシスタントです。
ユーザーから git diff が渡されます。
diff は unified 形式、または行内差分形式([-削除-]{{+追加+}}、… は省略した未変更部分)です。
あなたの仕事は「コミットメッセージを日本語で1つ書く」ことだけです。
コードの解説・修正案・質問への回答はしません。

{RULES}

出力はコミットメッセージ本文のみ。説明・前置き・引用符・コードフェンスは付けない。"""

RESTATE = "上の diff に対するコミットメッセージだけを出力してください(解説やコードは出力しない)。" \
          "複数の変更なら 1行目 + 空行 + 箇条書き、単一なら1行のみ。プレフィックスと「修正」「調整」は禁止。"

SUMMARY_SYSTEM = """あなたは git diff を読んで変更点を列挙するアシスタントです。
渡された diff の断片(全体の一部)について、何をどう変えたかを日本語の箇条書きで簡潔に列挙してください。
diff は unified 形式、または行内差分形式([-削除-]{+追加+}、… は省略した未変更部分)です。
ファイル名を添え、diff から読み取れることだけを書く。解説やコードは不要。"""


def summarize_chunk(chunk: str, model: str, idx: int, total: int) -> tuple[str, dict]:
    return oc.chat(
        oc.build_messages(SUMMARY_SYSTEM, f"### diff({idx}/{total})\n```diff\n{chunk}\n```",
                          "この断片の変更点を箇条書きで列挙してください。"),
        model, temperature=0.1, label=f"{model} 要約 {idx}/{total}",
    )


def generate(diff: str, model: str = MODEL, stat: str | None = None) -> tuple[str, dict]:
    """diffからコミットメッセージを生成し (メッセージ, 実行統計) を返す。evals/ からも呼ばれる本体。

    差分が大きい場合はファイル単位のチャンクを先に要約し、要約と変更ファイル一覧から
    メッセージを組み立てる(先頭切り捨てで後半の変更が落ちるのを防ぐ)。
    stat を渡すとそれを変更ファイル一覧に使う(行内差分は +/- 行が無く行数を数えられないため)。
    """
    chunks, diff_stat, skipped = oc.prepare_diff(diff)
    if not chunks:
        chunks, diff_stat = [diff], ""
    stat = diff_stat if stat is None else stat
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


_WORD_CHANGE_RE = re.compile(r"(\[-.*?-\]|\{\+.*?\+\})")


def shrink_word_diff(diff: str, keep: int = WORD_DIFF_KEEP) -> str:
    """行内差分の未変更部分を、変更箇所の前後 keep 文字だけ残して … に縮める。"""
    out = []
    for line in diff.splitlines():
        parts = _WORD_CHANGE_RE.split(line)  # 偶数番目が未変更部分、奇数番目が変更箇所
        if len(parts) > 1:
            last = len(parts) - 1
            for i in range(0, len(parts), 2):
                t = parts[i]
                if i == 0 and len(t) > keep:
                    parts[i] = "…" + t[-keep:]
                elif i == last and len(t) > keep:
                    parts[i] = t[:keep] + "…"
                elif 0 < i < last and len(t) > keep * 2:
                    parts[i] = t[:keep] + "…" + t[-keep:]
        out.append("".join(parts))
    return "\n".join(out) + "\n"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def staged_stat() -> str:
    """`git diff --cached --numstat` を diff_stat と同じ書式にする。"""
    lines = []
    for row in git("diff", "--cached", "--numstat").splitlines():
        added, removed, path = row.split("\t", 2)
        if not oc.NOISE_RE.search(path):
            lines.append(f"{path}  (+{added} -{removed})")
    return "\n".join(lines)


def main() -> None:
    diff = shrink_word_diff(git("diff", "--cached", "--no-color", *WORD_DIFF_ARGS))
    if not diff.strip():
        sys.exit("ステージ済みの変更がありません (git add してから実行)")
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))
    message, _ = generate(diff, model, staged_stat())
    print(message)


if __name__ == "__main__":
    main()
