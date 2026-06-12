---
name: night-mode
description: 夜間の安全な AI 自律稼働環境をセットアップし、claude --dangerously-skip-permissions を安全に使えるようにする
version: 1.0.0
---

# Night Mode セットアップスキル

このスキルは `claude --dangerously-skip-permissions` を使った夜間無人稼働を安全に行うための環境を準備します。

## セットアップ手順

以下を順番に実行してください。

### ステップ 1: Git リポジトリ確認

```bash
git status
```

- git リポジトリでない場合: 「git リポジトリ外では Night Mode は使用できません」と伝えて終了してください
- git リポジトリの場合: 次のステップへ

### ステップ 2: ブランチ確認

```bash
git branch --show-current
```

- `main`, `master`, `develop` などの保護ブランチの場合: ユーザーに警告し、作業ブランチへの切り替えを推奨してください
  - 例: `git checkout -b feat/night-work-$(date +%Y%m%d)`
- 既に作業ブランチの場合: 次のステップへ

### ステップ 3: セーフポイントコミット

未コミットの変更がある場合:

```bash
git add -A && git commit -m "checkpoint: night mode start $(date '+%Y-%m-%d %H:%M')"
```

変更がない場合はスキップ。

### ステップ 4: Night Mode フラグ作成

```bash
touch ~/.claude/night-mode-active
```

### ステップ 5: 完了メッセージ表示

以下の情報をユーザーへ表示してください:

---

**🌙 Night Mode が有効になりました**

**ブロック対象:**
| カテゴリ | 内容 |
|---------|------|
| ファイル破壊 | `rm -rf /`, `rm -rf ~/`, `rm -rf .` など |
| Git 履歴改ざん | `git push --force`, `git reset --hard` |
| デプロイ操作 | `terraform apply/destroy`, `cdk deploy`, `sam deploy`, `aws` CLI |
| インタラクティブ | `vi`, `vim`, `nano`, `less` など (ハング防止) |
| 機密ファイル編集 | `~/.ssh/*`, `~/.aws/credentials`, `*.pem`, `*.key` など |

**ログファイル:** `~/.claude/night-mode-log-YYYYMMDD.txt`

**起動コマンド:**
```bash
claude --dangerously-skip-permissions
```

**翌朝の確認:**
```bash
# 実行されたコマンドを確認
cat ~/.claude/night-mode-log-$(date +%Y%m%d).txt

# git で変更内容を確認
git log --oneline -20
git diff HEAD~1
```

**注意:** セッション終了時に Night Mode は自動解除されます。macOS 通知でも完了をお知らせします。

---
