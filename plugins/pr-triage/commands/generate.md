---
allowed-tools: Bash(gh pr list *), Bash(gh api *), Read
description: 複数リポジトリのオープンPRを取得し優先度でトリアージする
user-invocable: true
args:
  - name: repos
    description: "トリアージ対象のリポジトリ (スペース区切りで複数指定可, 例: owner/repo1 owner/repo2)"
    required: false
---

# PR Triage コマンド

複数リポジトリのオープン PR を取得し、優先度 (High / Medium / Low) を付与して一覧表示する。

## 実行手順

### ステップ1: 対象リポジトリの決定

以下の優先順で対象リポジトリを決定する:

1. **引数が指定されている場合**: `$ARGUMENTS` をスペース区切りで分割し、各要素をリポジトリとして使用する
2. **引数がない場合**: `~/.claude/pr-triage.local.md` を Read ツールで読み込み、YAML フロントマターの `repos` リストを使用する
3. **設定ファイルもない場合**: AskUserQuestion ツールでユーザーに対象リポジトリを質問する

### ステップ2: PR データの取得

各リポジトリに対して以下のコマンドを実行する。アクセスエラーが発生したリポジトリはスキップし、他のリポジトリの処理を続行する。

```bash
gh pr list --repo {REPO} --state open --json number,title,author,labels,createdAt,url,body,isDraft --limit 100
```

さらに、各 PR のリアクション数とコメント数を取得するために以下を実行する:

```bash
gh api repos/{OWNER}/{REPO}/pulls/{NUMBER} --jq '{comments: .comments, reactions: (.reactions.total_count // 0)}'
```

**重要**: パイプ (`|`) やサブシェル (`$(...)`) は使用不可。`gh` コマンドの `--jq` フラグや JSON 出力を直接解析すること。

### ステップ3: 優先度の判定

取得した PR データに対して、以下のルールを上から順に適用して優先度を判定する:

#### 判定ルール (優先順位順)

**1. bot PR の判定 (LOW 候補)**
- `author.login` が以下のいずれかに該当する場合、bot PR と判定する:
  - `renovate[bot]`
  - `dependabot[bot]`
  - ログイン名に `[bot]` を含む
- ただし、bot PR でもセキュリティ関連の場合は LOW にせず、次のルールで HIGH に昇格させる

**2. HIGH 優先度の判定**
以下のいずれかに該当する場合は HIGH:

- **ラベル条件**: ラベル名に以下のいずれかを含む (大文字小文字を区別しない):
  - `security`, `vulnerability`, `critical`, `urgent`, `P0`, `P1`, `hotfix`

- **タイトル・本文条件**: タイトルまたは本文に以下のいずれかを含む (大文字小文字を区別しない):
  - `CVE-`, `GHSA-`, `vulnerability`, `XSS`, `SQL injection`, `RCE`, `security`

- **エンゲージメント条件**: リアクション合計が 10 以上、またはコメント数が 15 以上

**3. MEDIUM 優先度 (デフォルト)**
- 上記いずれにも該当しない通常の PR

**4. LOW 優先度**
- bot PR かつセキュリティ関連でないもの

### ステップ4: 結果の出力

以下のフォーマットで結果を出力する。各グループ内は作成日が古い順にソートする。

```
## PR Triage 結果

対象リポジトリ: repo1, repo2, ...
合計PR数: N件 (High: n1 / Medium: n2 / Low: n3)

### 🔴 High Priority (n1件)

| # | リポジトリ | PR | 作成者 | 経過日数 | 理由 |
|---|-----------|-----|--------|---------|------|
| 1 | owner/repo | [#123 PRタイトル](URL) | author | 5日 | セキュリティラベル |

### 🟡 Medium Priority (n2件)

| # | リポジトリ | PR | 作成者 | 経過日数 | Draft |
|---|-----------|-----|--------|---------|-------|
| 1 | owner/repo | [#456 PRタイトル](URL) | author | 3日 | |

### 🟢 Low Priority (n3件)

| # | リポジトリ | PR | 作成者 | 経過日数 | 種別 |
|---|-----------|-----|--------|---------|------|
| 1 | owner/repo | [#789 依存関係更新](URL) | renovate[bot] | 1日 | bot |
```

**表示ルール:**
- Draft PR には 📝 マークを付ける
- High Priority の「理由」列には判定理由を簡潔に表示する (例: `セキュリティラベル`, `CVE検出`, `高エンゲージメント`)
- Low Priority の「種別」列には `bot` と表示する
- 経過日数は `createdAt` から現在日時までの差分を日数で表示する
- PR がゼロ件のグループは省略可能

## 注意事項

- `gh` CLI が認証済みであること
- リポジトリへのアクセス権限がない場合はスキップしてエラーメッセージを表示する
- PR 数が多い場合、リアクション・コメント数の取得は HIGH 判定に必要な場合のみ行い、効率化する
