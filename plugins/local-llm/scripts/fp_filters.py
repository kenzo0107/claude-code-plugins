"""LLM の指摘のうち、差分から機械的に誤りと言い切れる既知の誤検知パターンを除く。

プロンプトに「指摘しない」と書き足しても gemma4:12b は従わない(evals/RESULTS.md 2026-11-19)ため、
判定できるものは出力後にコードで落とす。危険な書き方を列挙して避けるのではなく、安全と確かめられた形だけを
除外する(列挙漏れが本物の脆弱性の見逃しになるため)。判定できないものは残す。
"""

import re
from collections.abc import Callable

import ollama_client as oc

RAW_SQL_CALL_RE = re.compile(r"\b(?:sql\.raw|knex\.raw|Prisma\.raw|[sS]equelize\.literal)\(\s*(\w+)\s*\)")
ANY_RAW_SQL_RE = re.compile(r"(?i)\.(?:raw|literal|unsafe)\w*\(|\$queryRawUnsafe|\$executeRawUnsafe")
TS_FUNCTION_RE = re.compile(r"^\s*function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)[^{]*\{")
PY_PRIVATE_DEF_RE = re.compile(r"^(\s*)def\s+(_\w+)\s*\(([^)]*)\)")
STRING_LITERAL_RE = re.compile(r"""^(?:'[^'\\]*'|"[^"\\]*"|`[^`$\\]*`)$""")


def _text(finding: dict, key: str) -> str:
    v = finding.get(key)
    return v if isinstance(v, str) else ""


def _files(diff: str) -> dict[str, list[str]]:
    """ファイルごとの追加行・文脈行の本文。削除行は呼び出し元の判定に使わない。"""
    return {f.path: [line[1:] for line in f.text.splitlines()
                     if line[:1] in ("+", " ") and not line.startswith("+++")]
            for f in oc.split_diff(diff)}


def _params(raw: str) -> list[str]:
    return [re.split(r"[:=]", p.strip(), maxsplit=1)[0].strip().lstrip("*") for p in raw.split(",") if p.strip()]


def _function_at(lines: list[str], use: int) -> tuple[str, list[str], range] | None:
    """use 行を本体に含む、export していない関数の (名前, 引数, 本体の行範囲)。

    export / 公開の関数は差分の外からも呼ばれ得て、呼び出し元を差分だけで確かめられないので対象にしない。
    """
    for start in range(use, -1, -1):
        if m := TS_FUNCTION_RE.match(lines[start]):
            depth = 0
            for end in range(start, len(lines)):
                depth += lines[end].count("{") - lines[end].count("}")
                if depth <= 0:
                    return (m[1], _params(m[2]), range(start, end + 1)) if use <= end else None
            return None
        if m := PY_PRIVATE_DEF_RE.match(lines[start]):
            indent = len(m[1])
            end = start + 1
            while end < len(lines) and (not lines[end].strip() or len(lines[end]) - len(lines[end].lstrip()) > indent):
                end += 1
            return (m[2], _params(m[3]), range(start, end)) if use < end else None
    return None


def _call_args(line: str, start: int) -> list[str] | None:
    """line[start] の '(' から対応する ')' までを、トップレベルのカンマで分けた引数にする。"""
    depth, quote, args, cur = 0, "", [], []
    for ch in line[start:]:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "'\"`":
            quote = ch
        elif ch in "([{":
            depth += 1
            if depth == 1:
                continue
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                args.append("".join(cur).strip())
                return [a for a in args if a]
        elif ch == "," and depth == 1:
            args.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    return None


def _receives_only_literals(name: str, index: int, lines: list[str], body: range) -> bool:
    """関数 name の index 番目の引数に、同じファイルのすべての呼び出しで文字列リテラルだけが渡っているか。"""
    calls = 0
    for i, line in enumerate(lines):
        if i == body.start:
            continue
        for m in re.finditer(rf"\b{re.escape(name)}\b", line):
            rest = line[m.end():]
            if not rest.lstrip().startswith("("):
                return False  # 関数を値として渡しており、実際の引数を追えない
            args = _call_args(line, m.end() + rest.index("("))
            if args is None or len(args) <= index or not STRING_LITERAL_RE.match(args[index]):
                return False
            calls += 1
    return calls > 0


def raw_sql_with_literal_args(finding: dict, diff: str) -> bool:
    """sql.raw() 等に渡す値が、同じファイルの呼び出しでは文字列リテラル(列名など)しか渡らない引数のとき。"""
    snippet = _text(finding, "snippet")
    idents = RAW_SQL_CALL_RE.findall(snippet)
    if not idents or len(idents) != len(ANY_RAW_SQL_RE.findall(snippet)):
        return False
    lines = _files(diff).get(_text(finding, "file"))
    if not lines:
        return False
    for ident in idents:
        uses = [i for i, line in enumerate(lines) if re.search(rf"\.(?:raw|literal)\(\s*{ident}\s*\)", line)]
        if not uses:
            return False
        for use in uses:
            fn = _function_at(lines, use)
            if fn is None:
                return False
            name, params, body = fn
            if ident not in params:
                return False
            if any(re.search(rf"\b{ident}\s*(?:[-+*/]?=)(?!=)", lines[i]) for i in body if i != body.start):
                return False  # 本体で引数を書き換えている
            if not _receives_only_literals(name, params.index(ident), lines, body):
                return False
    return True


SQL_TAGGED_TEMPLATE_RE = re.compile(r"\bsql`[^`]*`")
INJECTION_RE = re.compile(r"(?i)インジェクション|injection")


def sql_tagged_template_interpolation(finding: dict, diff: str) -> bool:
    """1 行の snippet で、sql`...${value}` への埋め込みを SQL インジェクションとする指摘。

    Drizzle・postgres.js・Slonik などの sql タグ付きテンプレートは ${} の値をプレースホルダにして送るので、
    文字列連結ではない。同じ行に raw/unsafe、タグの無いテンプレート、+ による連結があれば残す。
    """
    snippet = _text(finding, "snippet").strip()
    if "\n" in snippet or "${" not in snippet or not INJECTION_RE.search(_text(finding, "issue")):
        return False
    templates = SQL_TAGGED_TEMPLATE_RE.findall(snippet)
    if not any("${" in t for t in templates) or ANY_RAW_SQL_RE.search(snippet):
        return False
    rest = SQL_TAGGED_TEMPLATE_RE.sub("", snippet)
    return "`" not in rest and "+" not in rest


POLICY_LINE_RE = re.compile(r"(?i)\bcreate\s+policy\b|\bpgPolicy\s*\(")
NULL_COMPARISON_ISSUE_RE = re.compile(r"(?i)=\s*null|null\s*(?:との|の)?\s*比較|unknown|常に偽|always false")
# 未設定や NULL を許可へ倒し得る書き方。これらを含むポリシーは除外しない
FAIL_OPEN_RE = re.compile(r"(?i)\bcoalesce\s*\(|\bis\s+(?:not\s+)?distinct\b|[=<>]\s*''")
IS_NULL_RE = re.compile(r"(?i)\bis\s+null\b")
AND_COLUMN_IS_NULL_RE = re.compile(r"(?i)\band\s+[\w.\"]+\s+is\s+null\b")


def rls_policy_null_comparison(finding: dict, diff: str) -> bool:
    """RLS ポリシーで「NULL との比較が偽(Unknown)になる」という指摘。

    USING / WITH CHECK は NULL を偽として扱い行を拒否するので、未設定時に何も見えないのは安全側の挙動。
    IS NULL は「and 列 is null」で条件を足す形だけ認める(OR で NULL の行や未設定を許可する形を除外しないため)。
    """
    snippet = _text(finding, "snippet")
    if not POLICY_LINE_RE.search(snippet) or FAIL_OPEN_RE.search(snippet):
        return False
    if len(IS_NULL_RE.findall(snippet)) != len(AND_COLUMN_IS_NULL_RE.findall(snippet)):
        return False
    return bool(NULL_COMPARISON_ISSUE_RE.search(f"{_text(finding, 'issue')} {_text(finding, 'fix')}"))


CREATE_TABLE_RE = re.compile(r"(?i)^\s*create\s+table\b")
NOT_NULL_RE = re.compile(r"(?i)\bnot\s+null\b")
MIGRATION_DEFAULT_ISSUE_RE = re.compile(r"(?i)デフォルト|default|既存(?:の)?(?:データ|行|レコード)")


def not_null_in_create_table(finding: dict, diff: str) -> bool:
    """新規作成するテーブルの列定義の NOT NULL に「デフォルト値が無いと既存データで失敗する」という指摘。

    CREATE TABLE の時点では既存の行が無いので失敗しない。ALTER TABLE で列を足す行は残す。
    """
    snippet = _text(finding, "snippet").strip()
    if not snippet or "\n" in snippet or not NOT_NULL_RE.search(snippet) or re.search(r"(?i)\balter\b|\badd\b", snippet):
        return False
    if not MIGRATION_DEFAULT_ISSUE_RE.search(_text(finding, "issue")):
        return False
    lines = _files(diff).get(_text(finding, "file")) or []
    in_create_table = False
    for line in lines:
        if CREATE_TABLE_RE.match(line):
            in_create_table = True
        elif in_create_table and line.strip().startswith(");"):
            in_create_table = False
        elif in_create_table and line.strip() == snippet:
            return True
    return False


FILTERS: dict[str, Callable[[dict, str], bool]] = {
    "raw-sql-literal-args": raw_sql_with_literal_args,
    "sql-tagged-template": sql_tagged_template_interpolation,
    "rls-policy-null-comparison": rls_policy_null_comparison,
    "not-null-in-create-table": not_null_in_create_table,
}


def _matched_filter(finding: object, diff: str) -> str | None:
    if not isinstance(finding, dict):
        return None
    for name, is_false_positive in FILTERS.items():
        try:
            if is_false_positive(finding, diff):
                return name
        except Exception as e:  # noqa: BLE001 判定できない指摘は除外せず残す
            oc.log(f"[local-llm] 誤検知フィルタ {name} の判定に失敗したため指摘を残します: {e!r}")
    return None


def apply(findings: list[dict], diff: str) -> tuple[list[dict], list[dict]]:
    """(残す指摘, 除外した指摘) を返す。除外した指摘には suppressed_by にフィルタ名を入れる。"""
    kept, suppressed = [], []
    for f in findings:
        if hit := _matched_filter(f, diff):
            suppressed.append({**f, "suppressed_by": hit})
        else:
            kept.append(f)
    for f in suppressed:
        oc.log(f"[local-llm] 既知の誤検知として除外({f['suppressed_by']}): "
               f"{_text(f, 'file')}: {_text(f, 'snippet').strip()[:100]}")
    return kept, suppressed
