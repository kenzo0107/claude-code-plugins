# Settings Example

このファイルは設定の例です。実際の設定は `.claude/monthly-report.local.md` に記載してください。

## 設定ファイルの作成

プロジェクトルートの `.claude/monthly-report.local.md` を作成し、以下の内容を記載します：

```yaml
---
user_name: "山田太郎"
notion_database_url: "https://www.notion.so/your-database-id-here"
github_username: "example-user"
---
```

## 設定項目の説明

### user_name (必須)

月報に記載する名前。Notionページのタイトルに使用されます。

**例:**
```yaml
user_name: "山田太郎"
```

### notion_database_url (必須)

月報を投稿するNotionデータベースのURL。

**取得方法:**
1. Notionで月報データベースを開く
2. ブラウザのアドレスバーからURLをコピー
3. `?v=` 以降のビューIDは含めても含めなくてもOK

**例:**
```yaml
notion_database_url: "https://www.notion.so/your-database-id-here"
```

または

```yaml
notion_database_url: "https://www.notion.so/your-database-id-here?v=your-view-id-here"
```

### github_username (必須)

GitHub のユーザー名。PRを検索する際に使用されます。

**例:**
```yaml
github_username: "example-user"
```

## 完全な設定例

```yaml
---
user_name: "山田太郎"
notion_database_url: "https://www.notion.so/your-database-id-here"
github_username: "example-user"
---

# 月報設定

この設定ファイルは monthly-report プラグインで使用されます。

## メモ

- このファイルは .gitignore に含まれているため、リポジトリにコミットされません
- 設定を変更した場合、Claude Code を再起動する必要はありません
```

## トラブルシューティング

### 設定ファイルが見つからないエラー

```
❌ エラー: 設定ファイルが見つかりません
```

**原因:** `.claude/monthly-report.local.md` が存在しない

**対処:**
1. プロジェクトルートに `.claude` ディレクトリを作成
2. `.claude/monthly-report.local.md` を作成
3. 上記の設定例を参考に記載

### YAML解析エラー

```
❌ エラー: 設定ファイルの形式が不正です
```

**原因:** YAML frontmatter の記法が間違っている

**対処:**
- フロントマターは `---` で開始・終了すること
- キーと値の間にコロン `:` があること
- 文字列は `"` で囲むこと（推奨）

**正しい例:**
```yaml
---
user_name: "山田太郎"
---
```

**間違った例:**
```yaml
user_name: "山田太郎"  # フロントマター開始の --- がない
```

```yaml
---
user_name = "山田太郎"  # : ではなく = を使用
---
```

## セキュリティ上の注意

### Notion Integration Token について

Notion Integration Token は `.claude/monthly-report.local.md` には記載**しません**。

代わりに、Notion MCP の設定で環境変数として管理してください：

```bash
# ~/.zshrc または ~/.bashrc
export NOTION_API_KEY="secret_xxxxxxxxxxxxx"
```

詳細は Notion MCP のドキュメントを参照してください。

### .gitignore の確認

設定ファイルがリポジトリにコミットされないよう、`.gitignore` を確認してください：

```
# .gitignore
.claude/*.local.md
.claude/monthly-report-draft.md
```

## 設定の確認

設定が正しく読み込まれているか確認するには：

```
/monthly-report:add-weekly-entry
```

を実行してください。設定ファイルが正しく読み込まれている場合、ユーザー名とGitHubユーザー名が表示されます。
