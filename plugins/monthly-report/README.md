# monthly-report

エンジニアの月報作成を支援し、評価者に成果が伝わりやすい月報を効率的に作成するClaude Codeプラグイン。

## 概要

このプラグインは以下の機能を提供します：

- 📝 **週次記録**: GitHub PRを自動収集し、週次で活動を記録
- 📊 **月報生成**: 蓄積した記録からQ/L/D形式の月報を自動生成
- ✅ **品質レビュー**: 月報の品質を自動チェックし、改善提案
- 🔗 **Notion連携**: Notion月報データベースへの直接投稿・更新

## 前提条件

- Notion MCP の認証が完了していること
- GitHub の認証が完了していること（PRの取得に必要）
- `.claude/monthly-report.local.md` に設定を記載していること

## インストール

```bash
# このリポジトリをクローン
git clone https://github.com/your-username/claude-code-plugins.git

# Claude Code で有効化
cc --plugin-dir /path/to/claude-code-plugins/plugins/monthly-report
```

## 設定

`.claude/monthly-report.local.md` を作成し、以下の内容を記載してください：

```yaml
---
user_name: "山田太郎"
notion_database_url: "https://www.notion.so/your-database-id-here"
github_username: "example-user"
---
```

### 設定項目

| 項目 | 説明 | 必須 |
|------|------|------|
| `user_name` | 月報に記載する名前 | ✅ |
| `notion_database_url` | Notion月報データベースのURL | ✅ |
| `github_username` | GitHubユーザー名 | ✅ |

## 使い方

### 1. 週次で活動を記録

```
/monthly-report:add-weekly-entry
```

- 前回記録以降のGitHub PRを自動収集
- ローカルドラフト（`.claude/monthly-report-draft.md`）に追加

### 2. 月報を生成・投稿

```
/monthly-report:generate-report
```

- 蓄積したドラフトから月報を生成
- Q/L/Dを自動分類
- 品質レビューを実行
- Notionに投稿（確認あり）

#### オプション

- `--month YYYY-MM`: 対象月を指定（デフォルト: 今月）
- `--update`: 既存ページを更新（デフォルト: 新規作成）

## 月報フォーマット

このプラグインが生成する月報は以下の構造になります：

```markdown
## ① 今月のメインスコープ
- 主要なタスク・プロジェクト（チケット番号・結果を含む）

## ② Valueの証明（Q/L/Dから選択・混合でOK）
- **Q:** 品質向上の取り組み（具体的な数字・影響範囲）
- **L:** 効率化・レバレッジの工夫（工数削減・自動化など）
- **D:** 価値提供・意思決定（顧客価値・技術判断）

## ③ 進化・非停滞の証明
- 新しく学んだこと・成長した点

## ④ エビデンス
- PRリンク、ドキュメントリンク等
```

## トラブルシューティング

### Notion連携エラー

Notion MCPの認証を確認してください：

```bash
# Notion MCPの状態確認
cc mcp list
```

### PRが取得できない

GitHub認証とリポジトリへのアクセス権限を確認してください。

## ライセンス

MIT
