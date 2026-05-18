---
name: add-weekly-entry
description: GitHub PRを自動収集し、週次で活動を月報ドラフトに記録する
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__github__*
  - mcp__claude_ai_Notion__*
---

# Add Weekly Entry Command

このコマンドは、週次で自分のGitHub活動を収集し、月報ドラフトファイルに追加します。

## 実行手順

### 1. 設定ファイルの読み込み

`.claude/monthly-report.local.md` から以下の設定を読み込む：

```yaml
---
user_name: "山田太郎"
notion_database_url: "https://www.notion.so/your-database-id-here"
github_username: "example-user"
---
```

設定ファイルが存在しない場合は、エラーメッセージを表示し、README.mdの設定例を案内する。

### 2. 対象期間の決定

1. `.claude/monthly-report-draft.md` が存在する場合、ファイル内の最新の日付を確認
2. 最新日付以降の今日までをPR検索の対象期間とする
3. ドラフトファイルが存在しない場合、または日付が見つからない場合は、今月1日からを対象とする

### 3. GitHub PRの取得

GitHub MCPを使用して、以下の条件でPRを取得：

- author: 設定ファイルの `github_username`
- created: 対象期間内
- state: all（マージ済み、クローズ済み、オープン全て）

**重要**: GitHub MCPツール（`mcp__github__*`）を使用すること。直接GitHub APIを呼び出さない。

取得する情報：
- PRタイトル
- PR URL
- リポジトリ名
- マージ日（マージ済みの場合）
- ステータス（merged, closed, open）

### 4. PRリストの表示

取得したPRを以下の形式でユーザーに表示：

```
今週のPR (YYYY-MM-DD 以降):

[リポジトリ名]
- [merged] PRタイトル (#123) - YYYY-MM-DD
  https://github.com/org/repo/pull/123

- [open] PRタイトル (#456)
  https://github.com/org/repo/pull/456

全 X 件のPRが見つかりました。
これらを月報ドラフトに追加しますか？ (y/n)
```

### 5. ドラフトファイルへの追加

ユーザーが承認した場合（デフォルトでyes）：

1. `.claude/monthly-report-draft.md` を読み込む（存在しない場合は新規作成）
2. ファイルの末尾に以下の形式で追記：

```markdown
## Week of YYYY-MM-DD

### Pull Requests

#### [リポジトリ名]
- [PRタイトル](PR URL) - マージ日
  - TODO: このPRの意義・工夫した点を記入

#### [別リポジトリ名]
- [PRタイトル](PR URL) - マージ日
  - TODO: このPRの意義・工夫した点を記入

---
```

3. 追加完了メッセージを表示：

```
✅ X 件のPRを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

次のステップ:
- 各PRの「TODO」部分に、意義や工夫した点を記入してください
- 月報生成時は /monthly-report:generate-report を実行してください
```

## エラーハンドリング

### 設定ファイルが存在しない

```
❌ エラー: 設定ファイルが見つかりません

.claude/monthly-report.local.md を作成し、以下の内容を記載してください：

---
user_name: "あなたの名前"
notion_database_url: "https://www.notion.so/your-database-url"
github_username: "your-github-username"
---

詳細は README.md を参照してください。
```

### GitHub MCP未認証

```
❌ エラー: GitHub MCPに接続できません

GitHub認証を完了してください。
詳細: https://github.com/modelcontextprotocol/servers/tree/main/src/github
```

### PRが見つからない

```
ℹ️ 対象期間（YYYY-MM-DD 〜 YYYY-MM-DD）にPRが見つかりませんでした。

これは正常な場合があります：
- 対象期間内にPRを作成していない
- すでに全てのPRを記録済み

何もせずに終了します。
```

## 実装のヒント

### YAMLフロントマターの読み込み

```bash
# Readツールで.claude/monthly-report.local.mdを読み込む
# YAMLフロントマターを解析して変数に格納
```

### 日付の抽出

```bash
# ドラフトファイルから最新の "## Week of YYYY-MM-DD" を抽出
grep "^## Week of" .claude/monthly-report-draft.md | tail -1 | sed 's/## Week of //'
```

### GitHub MCP使用例

GitHub MCPツールを使用してPRを検索する際の例：

```
# search_pull_requests または list_pull_requests ツールを使用
# 正確なツール名はMCPサーバーの実装に依存するため、
# 利用可能なツールを確認してから使用すること
```

## 使用例

```
ユーザー: /monthly-report:add-weekly-entry

アシスタント:
設定を読み込みました: example-user

今週のPR (2026-05-12 以降):

[company-dev/main-app]
- [merged] ユーザー認証フローの改善 (#39965) - 2026-05-13
  https://github.com/company-dev/main-app/pull/39965

- [merged] API応答速度の最適化 (#39971) - 2026-05-14
  https://github.com/company-dev/main-app/pull/39971

[company-dev/career-api]
- [open] 求人API v2 実装 (#2716)
  https://github.com/company-dev/career-api/pull/2716

全 3 件のPRが見つかりました。
これらを月報ドラフトに追加しますか？ (y/n)

ユーザー: y

アシスタント:
✅ 3 件のPRを月報ドラフトに追加しました。
📝 ファイル: .claude/monthly-report-draft.md

次のステップ:
- 各PRの「TODO」部分に、意義や工夫した点を記入してください
- 月報生成時は /monthly-report:generate-report を実行してください
```

## 注意事項

- このコマンドは既存のドラフトファイルを上書きせず、追記のみ行う
- 同じPRを複数回追加することを防ぐ仕組みは実装しない（ユーザーが手動で管理）
- GitHub MCPの認証状態は事前に確認すること
- PRの取得に失敗した場合は、エラーメッセージを明確に表示すること
