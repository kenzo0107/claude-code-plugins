#!/usr/bin/env python3
"""コード差分を観点ファイル(ルール)に照らしてローカルLLMでプレレビューする汎用版。

観点ファイルを差し替えれば任意の言語・観点に使える。
指摘は参考情報(偽陽性あり得る)。決定的なツール(linter, gosec等)の代替ではない。

使い方:
    python3 code_review.py rules/go-security.md              # git diff HEAD の差分
    python3 code_review.py rules/go-security.md origin/main  # 指定refとの差分
    git diff main | python3 code_review.py rules/go-security.md -
    python3 code_review.py --auto origin/main                # 拡張子から観点を自動選択(複数言語可)
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "common")]
import ollama_client as oc  # noqa: E402

MODEL = os.environ.get("LOCAL_REVIEW_MODEL", oc.DEFAULT_MODEL)
# リポジトリでは code-review/rules/、プラグインでは <plugin>/rules/(scripts/ の1つ上)
RULES_DIR = next((d for d in (HERE / "rules", HERE.parent / "rules") if d.is_dir()), HERE / "rules")

# 拡張子 → 観点ファイル。--auto、pr_review、push フックが使う
RULES_BY_EXT = {
    (".go",): "go-security.md",
    (".py",): "python-security.md",
    (".rb", ".erb", ".rake"): "ruby-security.md",
    (".kt", ".kts"): "kotlin-android.md",
    (".ts", ".tsx", ".js", ".jsx", ".mjs"): "typescript-security.md",
}

SYSTEM = """あなたは経験豊富なコードレビュアーです。
ユーザーから「レビュー観点」と「差分」が渡されます。観点に照らして差分をレビューし、該当する問題のみを JSON で返してください。

ルール:
- 差分に現れた変更行(+ の行)だけを対象にする。既存コードや削除行の問題は指摘しない
- 観点に根拠がある指摘のみ。一般論・スタイルの好み・フォーマッタやリンタで検出できる事項は出さない
- 危険な API の無防備な使い方(検証なしの extractall、yaml.Loader、引数の URL をそのまま requests.get、
  文字列連結の SQL など)は、外部入力が届くかが差分から読めなくても指摘する。その場合 confidence は "low" にし、
  issue に「呼び出し元の入力次第」と明記する
- 逆に、既に安全な書き方(パラメータ化クエリ、safe_load、tempfile、検証済みの値、所有者でスコープした取得)に
  対して「もし型が違えば」「もしユーザー制御なら」と仮定を重ねて指摘しない(偽陽性の主因)
- 1つの問題は1件にまとめる(同じ箇所を複数のカテゴリで重複して挙げない)
- snippet には問題のある + 行をそのまま1行コピーする(位置特定に使う)
- 問題がなければ {"findings": []} を返す"""

# 注意: ここに JSON の例を書くと gemma4:12b は最初の1件で出力を打ち切る(evals/RESULTS.md 2026-09-12 の切り分け)。
# 形は JSON Schema(SCHEMA)が強制するので、再掲では「漏れなく列挙」だけを求める。
RESTATE = ("上の差分の + 行を観点に照らし、該当する問題を**漏れなく全て** findings に列挙してください"
           "(該当が無ければ空配列)。各件に snippet(該当する + 行)と confidence(high|low)を付ける。")

SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "category": {"type": "string"},
                    "issue": {"type": "string"},
                    "snippet": {"type": "string"},
                    "fix": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "low"]},
                },
                "required": ["file", "category", "issue", "snippet", "fix", "confidence"],
            },
        }
    },
    "required": ["findings"],
}


def get_diff(argv: list[str]) -> str:
    if argv and argv[0] == "-":
        return sys.stdin.read()
    base = argv[0] if argv else "HEAD"
    return subprocess.run(["git", "diff", base, "--no-color"], capture_output=True, text=True, check=True).stdout


def review(diff: str, rules: str, model: str = MODEL, exts: tuple[str, ...] | None = None) -> tuple[list[dict], dict]:
    """差分をレビューし (findings, 実行統計) を返す。evals/ からも呼ばれる本体。

    大きな差分はファイル単位のチャンクに分けて順にレビューし、結果を結合する。
    """
    chunks, _, skipped = oc.prepare_diff(diff, exts)
    if skipped:
        oc.log(f"[local-llm] 対象外として除外: {len(skipped)} ファイル")
    if not chunks:
        return [], {"model": model, "num_ctx": 0, "prompt_tokens": 0, "output_tokens": 0, "duration_s": 0.0}
    if len(chunks) > 1:
        oc.log(f"[local-llm] 差分が大きいため {len(chunks)} 分割でレビューします")

    findings: list[dict] = []
    stats_list = []
    for i, chunk in enumerate(chunks, 1):
        user = f"### レビュー観点\n{rules}\n\n### 差分\n```diff\n{chunk}\n```"
        result, stats = oc.chat_json(
            oc.build_messages(SYSTEM, user, RESTATE), model, SCHEMA,
            temperature=0.1, label=f"{model} {i}/{len(chunks)}" if len(chunks) > 1 else model,
        )
        findings.extend(result.get("findings", []))
        stats_list.append(stats)
    return dedupe(findings), oc.merge_stats(stats_list)


def dedupe(findings: list[dict]) -> list[dict]:
    """同一ファイル・同一 snippet の重複指摘を1件にまとめる(high を優先)。"""
    seen: dict[tuple, dict] = {}
    for f in findings:
        key = (f.get("file"), (f.get("snippet") or f.get("issue") or "").strip())
        if key not in seen or (f.get("confidence") == "high" and seen[key].get("confidence") != "high"):
            seen[key] = f
    return list(seen.values())


def rules_for_diff(diff: str) -> dict[str, tuple[str, ...]]:
    """diff に含まれるファイルの拡張子から、使う観点ファイル → 対象拡張子 を決める。"""
    paths = [f.path for f in oc.split_diff(diff)]
    selected = {}
    for exts, rule in RULES_BY_EXT.items():
        if any(p.endswith(exts) for p in paths) and (RULES_DIR / rule).exists():
            selected[rule] = exts
    return selected


def format_findings(findings: list[dict], model: str) -> str:
    if not findings:
        return f"指摘なし(ローカルLLM={model} によるプレレビュー)"
    out = [f"指摘 {len(findings)} 件(ローカルLLM={model}。偽陽性あり得ます):\n"]
    for i, f in enumerate(findings, 1):
        mark = "" if f.get("confidence") == "high" else " (低確度)"
        out.append(f"{i}. [{f.get('file', '?')}] {f.get('category', '?')}{mark}")
        if f.get("snippet"):
            out.append(f"   該当: {f['snippet'].strip()}")
        out.append(f"   問題: {f.get('issue', '')}")
        out.append(f"   修正: {f.get('fix', '')}\n")
    return "\n".join(out)


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        sys.exit("usage: code_review.py <rules.md | --auto> [base|-]")
    try:
        model = oc.resolve_model(MODEL, oc.DEFAULT_MODEL)
    except oc.OllamaError as e:
        sys.exit(str(e))

    if argv[0] == "--auto":
        diff = get_diff(argv[1:])
        if not diff.strip():
            print("差分がありません")
            return
        selected = rules_for_diff(diff)
        if not selected:
            print("対応する観点ファイルのある言語の差分がありません")
            return
        all_findings = []
        for rule, exts in selected.items():
            oc.log(f"[local-llm] {rule} で {'/'.join(exts)} をレビュー")
            findings, _ = review(diff, (RULES_DIR / rule).read_text(), model, exts)
            all_findings.extend(findings)
        print(format_findings(all_findings, model))
        return

    rules_path = Path(argv[0])
    if not rules_path.exists():
        sys.exit(f"観点ファイルが見つかりません: {rules_path}")
    diff = get_diff(argv[1:])
    if not diff.strip():
        print("差分がありません")
        return
    findings, _ = review(diff, rules_path.read_text(), model)
    print(format_findings(findings, model))


if __name__ == "__main__":
    main()
