---
name: generate-report
description: 蓄積したドラフトから月報を生成し、品質レビュー後にNotionに投稿する
argument-hint: "[--month YYYY-MM] [--update]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Task
  - AskUserQuestion
  - mcp__claude_ai_Notion__*
---

# Generate Report Command

このコマンドは、蓄積した週次ドラフトから月報を生成し、品質レビュー後にNotionに投稿します。

## 引数

- `--month YYYY-MM`: 対象月を指定（省略時は今月）
  - 例: `--month 2026-04` → 2026年4月の月報
  - `--month prev` または `--month last` → 前月
- `--update`: 既存ページを更新（省略時は新規作成）

## 実行手順

### 1. 対象月の決定

引数から対象月を決定：

```bash
# 引数なし → 今月 (date +%Y-%m)
# --month 2026-04 → 2026-04
# --month prev または --month last → 前月
```

対象月を `YYYY-MM` 形式で保持する（例: 2026-05）。

### 2. 設定ファイルの読み込み

`.claude/monthly-report.local.md` から設定を読み込む：

```yaml
user_name: "山田太郎"
notion_database_url: "https://www.notion.so/..."
github_username: "example-user"
```

### 3. ドラフトファイルの読み込み

`.claude/monthly-report-draft.md` を読み込み、対象月のエントリを抽出：

- 対象月の週次記録（`## Week of YYYY-MM-DD` で始まるセクション）を全て取得
- PR情報、TODO記入済みのコメントを整理

ドラフトが空、または対象月のエントリがない場合：

```
⚠️ 警告: 対象月（YYYY-MM）のドラフトエントリが見つかりません。

以下のいずれかを実行してください：
1. /monthly-report:add-weekly-entry で週次記録を追加
2. .claude/monthly-report-draft.md に手動で内容を記入

それでも続行しますか？ (y/n)
```

### 4. 月報の生成

monthly-report-best-practicesスキルを参照しながら、以下の構造で月報を生成：

```markdown
## ① 今月のメインスコープ
[ドラフトから主要なPR・タスクを抽出し、チケット番号・完了状態を含めて箇条書き]

## ② Valueの証明（Q/L/Dから選択・混合でOK）
[ドラフトの内容を分析し、Q/L/Dに自動分類]

### Q (Quality)
- [品質向上・リスク軽減の取り組みを具体的に記載]
- [数字・影響範囲を含める]

### L (Leverage)
- [効率化・自動化・再利用性向上の取り組みを記載]
- [工数削減・スケール効果を含める]

### D (Delivery)
- [ユーザー価値・ステークホルダー協働を記載]
- [ビジネスインパクトを含める]

## ③ 進化・非停滞の証明
[AIが週次記録から成長・進化のポイントを推測]
[確信が持てない場合は「TODO: ユーザーが手動記入」と記載]

## ④ エビデンス
[PRリンクをカテゴリごとに整理]

### [カテゴリ1] (重要度%)
- [PR #123: タイトル](URL)
- [PR #456: タイトル](URL)

### [カテゴリ2] (重要度%)
- [PR #789: タイトル](URL)
```

#### Q/L/D自動分類のルール

ドラフトの各エントリを分析し、以下の基準で分類：

- **Quality (Q)**:
  - キーワード: "バグ修正", "リファクタリング", "セキュリティ", "テスト", "品質", "安定性"
  - 影響範囲が大きい、リスク軽減

- **Leverage (L)**:
  - キーワード: "自動化", "効率化", "ツール作成", "CI/CD", "複数リポジトリ", "再利用"
  - 将来の工数削減、スケール効果

- **Delivery (D)**:
  - キーワード: "機能追加", "ユーザー", "要望", "リリース", "PdM", "ステークホルダー"
  - ユーザー価値、ビジネスインパクト

**重要**: 1つのPRが複数カテゴリに該当する場合、**主要な価値**で判断。
詳細は `skills/monthly-report-best-practices/references/qld-framework.md` を参照。

#### 進化・非停滞の推測

以下のパターンを検出：

- 新技術の採用（初めて触れたライブラリ、フレームワーク）
- 担当範囲の拡大（新しいリポジトリ、新しいドメイン）
- プロセス改善（新しいアプローチ、工夫）
- 能力向上（以前より速く、確実に実行）

確信度が低い場合は：
```
- TODO: ユーザーが手動記入（AIが推測: [推測内容]）
```

### 5. 品質レビューエージェントの起動

Task toolを使用して `review-monthly-report` エージェントを起動：

```
Task(
  subagent_type="review-monthly-report",
  prompt="生成した月報をレビューし、改善提案を提示してください",
  description="月報品質レビュー"
)
```

エージェントの結果を待ち、改善提案があれば表示：

```
📋 月報レビュー結果:

指摘事項:
- メインスコープにチケット番号が不足
- Q/L/Dに具体的な数字が少ない
- 「改善した」などの曖昧な表現が3箇所

修正案:
[具体的な修正案を表示]

この修正案を適用しますか？ (y/n)
```

ユーザーが承認した場合、修正を適用。

### 6. Notion投稿の確認

AskUserQuestionツールで投稿方法を確認：

```
月報の準備が完了しました。

【対象月】YYYY-MM
【ユーザー】[user_name]

次のアクションを選択してください:
1. Notionに新規投稿
2. Notion の既存ページを更新（ページURLを指定）
3. ローカルファイルのみ保存（Notionには投稿しない）
```

選択肢:
1. → 新規ページ作成
2. → 既存ページ更新（`--update` フラグ相当）
3. → `.claude/monthly-report-YYYY-MM.md` に保存して終了

### 7. Notion投稿

選択に応じて処理：

#### 7-1. 新規ページ作成

Notion MCPの `notion-create-pages` ツールを使用：

```
タイトル: 月報_[user_name]_[YYYYMM]
親: [notion_database_url]
内容: [生成した月報]
```

成功時:
```
✅ 月報をNotionに投稿しました

📄 タイトル: 月報_山田太郎_202605
🔗 URL: https://www.notion.so/...

ドラフトファイルをクリアしますか？ (y/n)
```

#### 7-2. 既存ページ更新

まず、対象月のページを検索：

```
Notion MCPの notion-search を使用:
検索クエリ: "月報_[user_name]_[YYYYMM]"
```

ページが見つかった場合、`notion-update-page` で更新。
見つからない場合、新規作成を提案。

#### 7-3. ローカルファイルのみ

`.claude/monthly-report-YYYY-MM.md` に保存：

```
✅ 月報をローカルファイルに保存しました

📄 ファイル: .claude/monthly-report-2026-05.md

後でNotionに投稿する場合:
/monthly-report:generate-report --month 2026-05 --update
```

### 8. ドラフトのクリア

ユーザーが承認した場合（デフォルトでyes）：

1. `.claude/monthly-report-draft.md` から対象月のエントリを削除
2. または、ファイル全体をバックアップして空にする

```
✅ ドラフトファイルをクリアしました

📦 バックアップ: .claude/monthly-report-draft-backup-YYYY-MM-DD.md
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

### 月報生成失敗

```
❌ エラー: 月報の生成に失敗しました

原因:
- ドラフトファイルの形式が不正
- 対象月のエントリが空

対処:
- .claude/monthly-report-draft.md を確認
- /monthly-report:add-weekly-entry で記録を追加
```

## 実装のヒント

### 対象月のエントリ抽出

```bash
# YYYY-MM 形式の月に該当する週次記録を抽出
# 例: 2026-05 → "## Week of 2026-05-*" を全て抽出
awk '/^## Week of 2026-05-/,/^## Week of [0-9]/' .claude/monthly-report-draft.md
```

### Notion MCP使用例

```
# ページ作成
notion-create-pages(
  title="月報_山田太郎_202605",
  parent_url="https://www.notion.so/...",
  content="[markdown content]"
)

# ページ検索
notion-search(
  query="月報_山田太郎_202605"
)

# ページ更新
notion-update-page(
  page_url="https://www.notion.so/...",
  content="[updated markdown content]"
)
```

## 使用例

### 例1: 今月の月報を新規作成

```
ユーザー: /monthly-report:generate-report

アシスタント:
対象月: 2026-05
設定を読み込みました: 山田太郎

ドラフトから月報を生成中...
✅ 月報を生成しました

📋 月報レビューを実行中...
✅ レビュー完了（指摘事項: 0件）

次のアクションを選択してください:
1. Notionに新規投稿
2. Notionの既存ページを更新
3. ローカルファイルのみ保存

ユーザー: 1

アシスタント:
✅ 月報をNotionに投稿しました
🔗 URL: https://www.notion.so/...

ドラフトファイルをクリアしますか？ (y/n)

ユーザー: y

アシスタント:
✅ ドラフトファイルをクリアしました
📦 バックアップ: .claude/monthly-report-draft-backup-2026-05-18.md
```

### 例2: 前月の月報を更新

```
ユーザー: /monthly-report:generate-report --month prev --update

アシスタント:
対象月: 2026-04
既存ページを検索中...

✅ 既存ページが見つかりました
📄 タイトル: 月報_山田太郎_202604
🔗 URL: https://www.notion.so/...

このページを更新しますか？ (y/n)

ユーザー: y

アシスタント:
✅ 月報を更新しました
🔗 URL: https://www.notion.so/...
```

## 注意事項

- 月報生成前に monthly-report-best-practices スキルを必ず参照すること
- Q/L/D分類は参考として提示し、ユーザーが最終確認できるようにする
- Notion投稿は必ずユーザーの確認を経てから実行すること
- ドラフトのクリアは必ずバックアップを作成してから行うこと
- レビューエージェントの結果は必ずユーザーに見せること
