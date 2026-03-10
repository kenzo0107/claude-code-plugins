# claude-plugins

Claude Code プラグイン集。

## プラグイン一覧

### pr-triage

複数リポジトリのオープン PR を取得し、優先度 (High / Medium / Low) を付与して一覧表示する。

#### インストール

```
# add marketplace
/plugin marketplace add https://github.com/kenzo0107/claude-plugins

# install plugin
/plugin install pr-triage@claude-code-plugins
```

#### 使い方

```
# 設定ファイルまたは対話で対象リポジトリを指定
/pr-triage:generate

# リポジトリを直接指定
/pr-triage:generate owner/repo1 owner/repo2
```

#### 設定ファイル

`~/.claude/pr-triage.local.md` に対象リポジトリを設定:

```yaml
---
repos:
  - owner/repo1
  - owner/repo2
---
```

#### 優先度ルール

| 優先度 | 条件 |
|--------|------|
| 🔴 High | セキュリティ関連ラベル・キーワード、高エンゲージメント |
| 🟡 Medium | 通常の PR |
| 🟢 Low | bot 作成 PR (セキュリティ関連を除く) |
