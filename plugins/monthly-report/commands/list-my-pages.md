---
name: list-my-pages
description: その月に自分が作成したNotionページ（レポート、構成図など）を取得し、月報ドラフトに追加する
argument-hint: "[--month YYYY-MM] [--add-to-draft]"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
  - mcp__claude_ai_Notion__*
---

# List My Pages Command

このコマンドは、その月に自分が作成したNotionページ（インフラ構成、レポート、ドキュメントなど）を一覧表示し、月報ドラフトに追加して成果報告に含められるようにします。

## 引数

- `--month YYYY-MM`: 特定の月に作成されたページのみを表示（省略時は今月）
  - 例: `--month 2026-05` → 2026年5月に作成されたページ
  - `--month prev` または `--month last` → 前月に作成されたページ
- `--add-to-draft`: 取得したページを月報ドラフトに自動追加（省略時は表示のみ）

## 実行手順

### 1. 設定ファイルの読み込み

`.claude/monthly-report.local.md` から設定を読み込む：

```yaml
user_name: "山田太郎"
notion_database_url: "https://www.notion.so/..."
github_username: "example-user"
```

### 2. 対象月の決定（--month指定時）

引数から対象月を決定：

```bash
# 引数なし → 全期間
# --month 2026-05 → 2026-05
# --month prev または --month last → 前月
```

対象月が指定された場合、検索クエリに含める。

### 3. Notionページの検索

Notion MCPツールを使用して、その月に作成したページを検索：

#### 検索戦略

1. **notion-get-users** で自分のユーザーIDを取得
2. **notion-search** または **notion-query-data-sources** で対象期間のページを検索
3. 作成日（created_time）でフィルタリング

#### 検索パラメータ

```javascript
// 対象期間の計算
const targetMonth = "2026-05"; // --month引数から取得
const startDate = "2026-05-01T00:00:00Z";
const endDate = "2026-05-31T23:59:59Z";

// notion-search または notion-query-data-sources を使用
// フィルタ条件:
// - created_time が startDate から endDate の間
// - created_by が自分のユーザーID
```

**重要**:
- Notion MCPの `notion-get-self` または `notion-get-users` で自分のユーザー情報を取得
- `notion-search` で全ページを取得し、作成日でフィルタリング
- データベース指定がある場合は `notion-query-data-sources` を使用

### 4. ページの分類とフィルタリング

取得したページを以下のカテゴリに自動分類：

- **📊 レポート・分析**: タイトルに「レポート」「分析」「調査」「報告」を含む
- **🏗️ インフラ・構成**: タイトルに「構成」「アーキテクチャ」「infrastructure」「設計」を含む
- **📚 ドキュメント**: タイトルに「手順」「マニュアル」「ガイド」「仕様」を含む
- **📝 その他**: 上記以外のページ

**月報ページの除外**:
- タイトルが「月報_」で始まるページは除外
- 既に月報として管理されているため

### 5. ページ一覧の表示

取得したページをカテゴリ別に表示：

```
📄 2026-05 に作成したNotionページ:

【📊 レポート・分析】(2件)
1. ☑️ AWS コスト分析レポート
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-03

2. ☑️ パフォーマンス改善調査結果
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-15

【🏗️ インフラ・構成】(1件)
3. ☑️ 本番環境ネットワーク構成図
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-10

【📚 ドキュメント】(1件)
4. ☑️ デプロイ手順書 v2.0
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-20

全 4 件のページが見つかりました。

次のアクションを選択してください:
1. 選択したページを月報ドラフトに追加
2. 全ページを月報ドラフトに追加
3. ページの内容を表示
4. 何もしない
```

### 6. ユーザーアクションの処理

AskUserQuestionツールで次のアクションを確認：

#### 選択肢1: 選択したページを月報ドラフトに追加

```
月報ドラフトに追加するページ番号を選択してください (複数選択可、カンマ区切り):
例: 1,3,4
```

ユーザーが番号を選択した場合：

1. 選択したページの情報を取得
2. `.claude/monthly-report-draft.md` に以下の形式で追加：

```markdown
## Week of YYYY-MM-DD

### Notion Documents Created

#### 📊 レポート・分析
- [AWS コスト分析レポート](https://www.notion.so/...) - 2026-05-03
  - TODO: このドキュメントの目的・成果を記入

#### 🏗️ インフラ・構成
- [本番環境ネットワーク構成図](https://www.notion.so/...) - 2026-05-10
  - TODO: このドキュメントの目的・成果を記入

---
```

3. 追加完了メッセージを表示：

```
✅ 3 件のNotionページを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

次のステップ:
- 各ページの「TODO」部分に、目的や成果を記入してください
- 月報生成時は /monthly-report:generate-report を実行してください
```

#### 選択肢2: 全ページを月報ドラフトに追加

全てのページを自動的にドラフトに追加：

```
✅ 4 件のNotionページを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

カテゴリ別の内訳:
- 📊 レポート・分析: 2件
- 🏗️ インフラ・構成: 1件
- 📚 ドキュメント: 1件

次のステップ:
- 各ページの「TODO」部分に、目的や成果を記入してください
- 月報生成時は /monthly-report:generate-report を実行してください
```

#### 選択肢3: ページの内容を表示

```
表示するページ番号を入力してください (1-N):
```

ユーザーが番号を選択した場合：

1. `notion-fetch` ツールでページ内容を取得
2. Markdown形式で内容を表示（先頭100行程度）

```markdown
## AWS コスト分析レポート

🔗 https://www.notion.so/...
📅 作成日: 2026-05-03

---

[ページの内容をMarkdownで表示（先頭部分）]

---

オプション:
1. このページを月報ドラフトに追加
2. 全内容をローカルファイルに保存
3. 戻る
```

#### 選択肢4: 何もしない

そのまま終了。

### 7. 自動追加モード（--add-to-draft フラグ）

`--add-to-draft` フラグが指定された場合、確認なしで全ページをドラフトに追加：

```bash
/monthly-report:list-my-pages --month 2026-05 --add-to-draft
```

実行結果：

```
📄 2026-05 に作成したNotionページを検索中...

✅ 4 件のNotionページが見つかりました。
月報ドラフトに自動追加します...

カテゴリ別の内訳:
- 📊 レポート・分析: 2件
- 🏗️ インフラ・構成: 1件
- 📚 ドキュメント: 1件

✅ 全てのページを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

次のステップ:
- 各ページの「TODO」部分に、目的や成果を記入してください
- 月報生成時は /monthly-report:generate-report を実行してください
```

## エラーハンドリング

### 設定ファイルが存在しない

```
❌ エラー: 設定ファイルが見つかりません

詳細は /monthly-report:add-weekly-entry のエラーメッセージを参照
```

### Notion MCP未認証

```
❌ エラー: Notion MCPに接続できません

Notion認証を完了してください:
1. Notion Integration を作成
2. データベースに Integration を共有
3. MCP サーバーを設定

詳細: README.md を参照
```

### ページが見つからない

```
ℹ️ 自分が作成した月報ページが見つかりませんでした。

考えられる原因:
- まだ月報を作成していない
- タイトル形式が「月報_[user_name]_[YYYYMM]」と異なる
- Notionデータベースへのアクセス権限がない

次のステップ:
1. /monthly-report:generate-report で月報を作成
2. Notionでタイトル形式を確認
3. データベースのアクセス権限を確認
```

## 実装のヒント

### Notion MCP使用例

```javascript
// ページ検索
notion-search({
  query: "月報_山田太郎",
  // データベースURLを指定することで、そのデータベース内のみを検索
  filter: {
    database: notion_database_url
  }
})

// ページ取得
notion-fetch({
  url: "https://www.notion.so/..."
})

// データソースクエリ（データベース全体）
notion-query-data-sources({
  database_url: notion_database_url
})
```

### タイトルのパース

```bash
# "月報_山田太郎_202605" から YYYY-MM を抽出
echo "月報_山田太郎_202605" | grep -oE '[0-9]{6}' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)/\1-\2/'
# 出力: 2026-05
```

## 使用例

### 例1: 今月作成したNotionページを一覧表示

```
ユーザー: /monthly-report:list-my-pages

アシスタント:
設定を読み込みました: 山田太郎

📄 2026-05 に作成したNotionページ:

【📊 レポート・分析】(2件)
1. ☑️ AWS コスト分析レポート
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-03

2. ☑️ パフォーマンス改善調査結果
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-15

【🏗️ インフラ・構成】(1件)
3. ☑️ 本番環境ネットワーク構成図
   🔗 https://www.notion.so/...
   📅 作成日: 2026-05-10

全 3 件のページが見つかりました。

次のアクションを選択してください:
1. 選択したページを月報ドラフトに追加
2. 全ページを月報ドラフトに追加
3. ページの内容を表示
4. 何もしない

ユーザー: 2

アシスタント:
✅ 3 件のNotionページを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

カテゴリ別の内訳:
- 📊 レポート・分析: 2件
- 🏗️ インフラ・構成: 1件

次のステップ:
- 各ページの「TODO」部分に、目的や成果を記入してください
- 月報生成時は /monthly-report:generate-report を実行してください
```

### 例2: 特定月のページを自動追加

```
ユーザー: /monthly-report:list-my-pages --month 2026-04 --add-to-draft

アシスタント:
設定を読み込みました: 山田太郎

📄 2026-04 に作成したNotionページを検索中...

✅ 2 件のNotionページが見つかりました。
月報ドラフトに自動追加します...

カテゴリ別の内訳:
- 📚 ドキュメント: 2件

✅ 全てのページを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md
```

### 例3: 選択したページのみを追加

```
ユーザー: /monthly-report:list-my-pages --month 2026-05

アシスタント:
[ページ一覧を表示]

次のアクションを選択してください:
1. 選択したページを月報ドラフトに追加
2. 全ページを月報ドラフトに追加
3. ページの内容を表示
4. 何もしない

ユーザー: 1

アシスタント:
月報ドラフトに追加するページ番号を選択してください (複数選択可、カンマ区切り):
例: 1,3

ユーザー: 1,3

アシスタント:
✅ 2 件のNotionページを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

追加したページ:
- AWS コスト分析レポート
- 本番環境ネットワーク構成図
```

### 例4: ページが見つからない場合

```
ユーザー: /monthly-report:list-my-pages --month 2026-03

アシスタント:
設定を読み込みました: 山田太郎

ℹ️ 2026-03 に作成したNotionページが見つかりませんでした。

考えられる原因:
- 対象月にNotionページを作成していない
- Notionワークスペースへのアクセス権限がない

次のステップ:
- Notionで直接確認
- 期間を変更して再度検索
```

## 注意事項

- Notion MCPの検索機能を使用するため、ワークスペース全体へのアクセス権限が必要
- 作成日（created_time）でのフィルタリングが正確に機能するためには、Notion MCPが作成日情報を提供する必要がある
- 月報ページ（`月報_`で始まるタイトル）は自動的に除外される
- カテゴリ分類はタイトルベースの推測のため、不正確な場合は手動で調整すること
- `--add-to-draft` フラグを使用すると、確認なしで全ページが追加されるため注意
- 同じページを複数回追加することを防ぐ仕組みは実装していない（ユーザーが手動で管理）
- 大量のページがある場合、検索に時間がかかる可能性がある

## ワークフロー例

### 月末の月報作成フロー

```bash
# 1. 今月作成したNotionページを確認・追加
/monthly-report:list-my-pages --add-to-draft

# 2. 今月のGitHub PRを追加
/monthly-report:add-weekly-entry

# 3. ドラフトを編集（各TODO部分を記入）
# .claude/monthly-report-draft.md を編集

# 4. 月報を生成・投稿
/monthly-report:generate-report
```

このフローにより、GitHub活動だけでなく、Notionで作成したドキュメント・レポート・構成図なども含めた包括的な月報を作成できます。
