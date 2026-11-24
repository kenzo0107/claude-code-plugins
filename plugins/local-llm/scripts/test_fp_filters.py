"""python3 -m unittest discover -s tools/code-review で実行する。"""

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent.parent / "common")]
import fp_filters  # noqa: E402
import ollama_client as oc  # noqa: E402

oc.QUIET = True

SCHEMA = "src/db/schema.ts"


def file_diff(path: str, body: str) -> str:
    added = "".join(f"+{line}\n" for line in body.strip("\n").splitlines())
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -0,0 +1 @@\n{added}"


HELPERS = file_diff(SCHEMA, """
const currentUserId = sql`nullif(current_setting('app.user_id', true), '')::bigint`;
function isSelf(column: string): SQL {
  return sql`${sql.raw(column)} = ${currentUserId}`;
}
function canSeeOrder(orderId: string): SQL {
  return sql`exists (select 1 from orders o where o.id = ${sql.raw(orderId)} and ${isSelf('o.owner_id')})`;
}
    pgPolicy('orders_select', { for: 'select', using: isSelf('orders.owner_id') }),
    pgPolicy('items_select', { for: 'select', using: canSeeOrder("items.order_id") }),
""")
IS_SELF_RAW = "  return sql`${sql.raw(column)} = ${currentUserId}`;"


def finding(snippet: str, issue: str = "SQLインジェクションの危険性", fix: str = "", file: str = SCHEMA) -> dict:
    return {"file": file, "category": "インジェクション", "issue": issue,
            "snippet": snippet, "fix": fix, "confidence": "high"}


class RawSqlWithLiteralArgsTest(unittest.TestCase):
    def test_列名リテラルしか渡らない補助関数のsql_rawは誤検知として除く(self):
        for snippet in (IS_SELF_RAW,
                        "  return sql`exists (select 1 from orders o where o.id = ${sql.raw(orderId)}"):
            with self.subTest(snippet=snippet):
                self.assertTrue(fp_filters.raw_sql_with_literal_args(finding(snippet), HELPERS))

    def test_呼び出し元が変数を渡していれば残す(self):
        diff = HELPERS + "+  const rows = await db.select().where(isSelf(req.query.column));\n"
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding(IS_SELF_RAW), diff))

    def test_関数を値として渡していて引数を追えなければ残す(self):
        diff = HELPERS + "+  const checks = columns.map(isSelf);\n"
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding(IS_SELF_RAW), diff))

    def test_exportした関数は差分外から呼ばれ得るので残す(self):
        diff = file_diff(SCHEMA, """
export function orderBy(column: string): SQL {
  return sql`order by ${sql.raw(column)}`;
}
orderBy('created_at');
""")
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding("  return sql`order by ${sql.raw(column)}`;"), diff))

    def test_差分内に呼び出しが無ければ残す(self):
        diff = file_diff(SCHEMA, """
function orderBy(column: string): SQL {
  return sql`order by ${sql.raw(column)}`;
}
""")
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding("  return sql`order by ${sql.raw(column)}`;"), diff))

    def test_関数の外でsql_rawに渡していれば残す(self):
        snippet = "await db.execute(sql`SELECT * FROM t ORDER BY ${sql.raw(column)}`);"
        for diff in (
            file_diff("a.ts", "function label(column: string) { return column.trim(); }\nlabel('id');")
            + file_diff("b.ts", "const column = req.query.sort as string;\n" + snippet),
            file_diff("b.ts", "function label(column: string) {\n  return column.trim();\n}\nlabel('id');\n"
                      "const column = req.query.sort as string;\n" + snippet),
        ):
            with self.subTest(diff=diff):
                self.assertFalse(fp_filters.raw_sql_with_literal_args(finding(snippet, file="b.ts"), diff))

    def test_クラスメソッドのように関数定義として認識できなければ残す(self):
        diff = file_diff("repo.ts", """
function label(column: string) { return column.toUpperCase(); }
label("name");
class Repo {
  find(column: string) {
    return db.select().from(t).orderBy(sql.raw(column));
  }
}
await repo.find(req.query.sort);
""")
        snippet = "    return db.select().from(t).orderBy(sql.raw(column));"
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding(snippet, file="repo.ts"), diff))

    def test_同じsnippetにほかのraw呼び出しがあれば残す(self):
        snippet = "  return sql`${sql.raw(column)} ${sql.raw('x' + req.query.q)}`;"
        diff = file_diff(SCHEMA, f"function isSelf(column: string): SQL {{\n{snippet}\n}}\nisSelf('a.id');")
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding(snippet), diff))

    def test_本体で引数を書き換えていれば残す(self):
        diff = file_diff(SCHEMA, """
function f(column: string): SQL {
  column = req.query.sort;
  return sql.raw(column);
}
f('id');
""")
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding("  return sql.raw(column);"), diff))

    def test_sql_rawを含まない指摘には関与しない(self):
        self.assertFalse(fp_filters.raw_sql_with_literal_args(finding("  db.execute(`select ${id}`)"), HELPERS))


class SqlTaggedTemplateInterpolationTest(unittest.TestCase):
    def test_sqlタグ付きテンプレートへの値の埋め込みは誤検知として除く(self):
        snippet = "  await tx.execute(sql`select set_config('app.user_id', ${String(userId)}, true)`);"
        self.assertTrue(fp_filters.sql_tagged_template_interpolation(finding(snippet), ""))

    def test_同じ行に素のSQLとして埋め込む書き方があれば残す(self):
        for snippet in (
            "  await db.execute(sql`select * from t order by ${sql.raw(req.query.sort)}`);",
            "  await sql.unsafe(`select * from t where id = ${req.params.id}`);",
            "  await prisma.$queryRawUnsafe(`SELECT * FROM t WHERE ${where}`, sql`x ${y}`);",
            "  await db.execute(sql`SELECT * FROM ${tbl}` + ' WHERE name = ' + name);",
            "  const a = await sql`SELECT 1 WHERE id = ${id}`; const b = await pool.query(`SELECT '${name}'`);",
        ):
            with self.subTest(snippet=snippet):
                self.assertFalse(fp_filters.sql_tagged_template_interpolation(finding(snippet), ""))

    def test_複数行のsnippetは残す(self):
        snippet = ("const a = await sql`SELECT 1 WHERE id = ${id}`;\n"
                   "const b = await pool.query(`SELECT * FROM t WHERE name = '${name}'`);")
        self.assertFalse(fp_filters.sql_tagged_template_interpolation(finding(snippet), ""))

    def test_タグの無いテンプレートリテラルでのSQL組み立ては残す(self):
        snippet = "  await pool.query(`select * from t where id = ${req.params.id}`);"
        self.assertFalse(fp_filters.sql_tagged_template_interpolation(finding(snippet), ""))

    def test_インジェクション以外の指摘には関与しない(self):
        snippet = "  await tx.execute(sql`select * from t where id = ${id}`);"
        self.assertFalse(fp_filters.sql_tagged_template_interpolation(finding(snippet, issue="await 忘れ"), ""))


POLICY = ("CREATE POLICY \"orders_update\" ON \"orders\" AS PERMISSIVE FOR UPDATE TO public USING "
          "(orders.owner_id = nullif(current_setting('app.user_id', true), '')::bigint and orders.closed_at is null "
          "or exists (select 1 from staff s where s.id = nullif(current_setting('app.user_id', true), '')::bigint))")
NULL_ISSUE = "current_setting が null の場合 = null の比較は常に偽(Unknown)となり、権限チェックが正しく動作しない"


class RlsPolicyNullComparisonTest(unittest.TestCase):
    def test_ポリシーでNULLとの比較が偽になるという指摘は誤検知として除く(self):
        for snippet in (POLICY, "    pgPolicy('orders_select', { for: 'select', using: isSelf('orders.owner_id') }),"):
            with self.subTest(snippet=snippet):
                self.assertTrue(fp_filters.rls_policy_null_comparison(finding(snippet, NULL_ISSUE), ""))

    def test_未設定やNULLの行を許可へ倒し得るポリシーは残す(self):
        for snippet in (
            "CREATE POLICY p ON t USING (current_setting('app.user_id', true) is null or owner_id = 1)",
            "CREATE POLICY p ON t USING ((current_setting('app.tenant_id', true)) IS NULL OR tenant_id = 1)",
            "CREATE POLICY p ON t USING (nullif(current_setting('app.user_id', true), '') IS NULL)",
            "CREATE POLICY p ON t USING (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id')::uuid)",
            "CREATE POLICY p ON t USING (COALESCE(tenant_id = current_setting('app.tenant_id', true)::uuid, true))",
            "CREATE POLICY p ON t USING (current_setting('app.tenant_id', true) IS NOT DISTINCT FROM NULL OR x)",
            "CREATE POLICY p ON t USING (current_setting('app.role', true) = '' OR owner = current_user)",
        ):
            with self.subTest(snippet=snippet):
                self.assertFalse(fp_filters.rls_policy_null_comparison(finding(snippet, NULL_ISSUE), ""))

    def test_ポリシー以外の行のNULLの指摘は残す(self):
        for snippet in ("SELECT * FROM orders WHERE deleted_at = NULL",
                        "SELECT * FROM a JOIN b USING (id) WHERE b.deleted_at = NULL"):
            with self.subTest(snippet=snippet):
                self.assertFalse(fp_filters.rls_policy_null_comparison(finding(snippet, NULL_ISSUE), ""))

    def test_NULL比較についての指摘でなければ残す(self):
        for issue in ("UPDATE のポリシーに WITH CHECK が無く、所有者を書き換えられる",
                      "owner_id が NULL の行は所有者が無く、誰からも更新できない"):
            with self.subTest(issue=issue):
                self.assertFalse(fp_filters.rls_policy_null_comparison(finding(POLICY, issue), ""))


MIGRATION = "drizzle/0001_create_orders.sql"
DEFAULT_ISSUE = "NOT NULL 制約を追加しているが、既存データが存在する場合デフォルト値の指定がないため移行に失敗する"


class NotNullInCreateTableTest(unittest.TestCase):
    def test_新規テーブルの列定義のNOT_NULLへのデフォルト値の指摘は誤検知として除く(self):
        diff = file_diff(MIGRATION, '''
CREATE TABLE "orders" (
	"id" uuid PRIMARY KEY NOT NULL,
	"owner_id" bigint NOT NULL
);
''')
        f = finding('"owner_id" bigint NOT NULL', DEFAULT_ISSUE, file=MIGRATION)
        self.assertTrue(fp_filters.not_null_in_create_table(f, diff))

    def test_既存テーブルへの列追加は残す(self):
        snippet = 'ALTER TABLE "orders" ADD COLUMN "owner_id" bigint NOT NULL;'
        diff = file_diff(MIGRATION, snippet)
        self.assertFalse(fp_filters.not_null_in_create_table(finding(snippet, DEFAULT_ISSUE, file=MIGRATION), diff))

    def test_CREATE_TABLEの外にある同じ行は残す(self):
        diff = file_diff(MIGRATION, '''
CREATE TABLE "orders" (
	"id" uuid PRIMARY KEY NOT NULL
);
ALTER TABLE "orders"
	"owner_id" bigint NOT NULL
''')
        f = finding('"owner_id" bigint NOT NULL', DEFAULT_ISSUE, file=MIGRATION)
        self.assertFalse(fp_filters.not_null_in_create_table(f, diff))

    def test_デフォルト値や既存データ以外の指摘は残す(self):
        diff = file_diff(MIGRATION, 'CREATE TABLE "orders" (\n\t"note" text NOT NULL\n);')
        f = finding('"note" text NOT NULL', "空文字を許してしまうので CHECK 制約が要る", file=MIGRATION)
        self.assertFalse(fp_filters.not_null_in_create_table(f, diff))


class ApplyTest(unittest.TestCase):
    def test_除外した指摘にはフィルタ名を付けて返し残りはそのまま返す(self):
        raw = finding(IS_SELF_RAW)
        real = finding("  const rows = await db.execute(`select * from t where id = ${req.params.id}`);")

        kept, suppressed = fp_filters.apply([raw, real], HELPERS)

        self.assertEqual(kept, [real])
        self.assertEqual([f["suppressed_by"] for f in suppressed], ["raw-sql-literal-args"])

    def test_想定外の型の指摘は除外せず残す(self):
        odd = [{"file": SCHEMA, "snippet": None, "issue": None}, {"snippet": ["a"]}, "not a dict"]

        kept, suppressed = fp_filters.apply(odd, HELPERS)

        self.assertEqual(kept, odd)
        self.assertEqual(suppressed, [])


if __name__ == "__main__":
    unittest.main()
