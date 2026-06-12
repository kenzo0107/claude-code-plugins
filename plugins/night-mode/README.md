# night-mode

`claude --dangerously-skip-permissions` を夜間の無人稼働で安全に使うための Claude Code プラグインです。

## 概要

夜間に AI を無人稼働させる際、`--dangerously-skip-permissions` は全ての確認プロンプトをスキップするため、
破壊的操作が意図せず実行されるリスクがあります。

このプラグインは **Hooks による安全ガード** と **フラグファイルによる on/off 切り替え** で主要リスクをカバーします。

## 機能

### ブロック対象

| カテゴリ | 内容 |
|---------|------|
| ファイル破壊 | `rm -rf /`, `rm -rf ~/`, `rm -rf .` など |
| Git 履歴改ざん | `git push --force`, `git reset --hard` |
| デプロイ操作 | `terraform apply/destroy`, `cdk deploy`, `sam deploy`, `aws` CLI |
| クラウド CLI | `gcloud`, `gsutil`, `bq`, `az`, `doctl`, `heroku`, `firebase`, `vercel`, `netlify`, `pulumi`, `serverless` |
| Kubernetes / Helm | `kubectl apply/create/delete/patch/...`, `helm install/upgrade/uninstall/...` |
| GitHub CLI 変更操作 | `gh repo create/delete`, `gh pr create/merge`, `gh issue create/close`, `gh release create`, `gh workflow run`, `gh secret/variable set` など |
| パッケージ公開 | `npm publish`, `yarn publish`, `cargo publish`, `gem push`, `twine upload`, `poetry publish` |
| Docker レジストリ | `docker push`, `docker image push`, `docker manifest push` |
| インタラクティブ | `vi`, `vim`, `nano`, `less` など（無人実行でハング） |
| 機密ファイル編集 | `~/.ssh/*`, `~/.aws/credentials`, `*.pem`, `*.key` など |

### その他の機能

- **実行ログ記録**: 夜間に実行した Bash コマンドを `~/.claude/night-mode-log-YYYYMMDD.txt` に記録
- **macOS 通知**: セッション終了時に完了通知を送信
- **自動解除**: セッション終了時に Night Mode を自動解除

## 使い方

### 1. Night Mode を有効化

夜間作業を始める前に、対象プロジェクトのディレクトリで実行:

```
/night-mode
```

スキルが以下を自動実行します:
- Git リポジトリ確認
- 保護ブランチ（main/master/develop）チェックと警告
- 未コミット変更のセーフポイントコミット
- Night Mode フラグ (`~/.claude/night-mode-active`) の作成

### 2. 夜間セッション起動

```bash
claude --dangerously-skip-permissions
```

### 3. 翌朝の確認

```bash
# 実行されたコマンドを確認
cat ~/.claude/night-mode-log-$(date +%Y%m%d).txt

# git で変更内容を確認
git log --oneline -20
```

## 仕組み

```
~/.claude/night-mode-active  (フラグファイル)
         │
         ├── 存在する → 全 hook のガードが有効
         └── 存在しない → hook はスルー（通常モード）
```

セッション終了時 (Stop hook) にフラグを自動削除するため、翌日からは通常モードで動作します。

## Hooks 構成

| Hook | タイミング | スクリプト |
|------|-----------|-----------|
| PreToolUse (Bash) | Bash コマンド実行前 | `night-mode-bash-guard.sh` |
| PreToolUse (Edit/Write) | ファイル編集前 | `night-mode-file-guard.sh` |
| PostToolUse (Bash) | Bash コマンド実行後 | `night-mode-logger.sh` |
| Stop | セッション終了時 | `night-mode-stop.sh` |
