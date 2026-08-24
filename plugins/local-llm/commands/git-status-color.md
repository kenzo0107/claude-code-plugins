---
allowed-tools: Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/git_status_color.sh*), Bash(git status *)
description: git status をステージ済み(緑)/未ステージ・未追跡(赤)に色分けして表示する(純粋なgit操作。ローカルLLMは使わない)
user-invocable: true
---

# git-status-color: git status の色分け表示

`git status` の内容を、ステージ済み(緑)/未ステージ・未追跡(赤)に色分けして表示する。
1ファイルが両方の状態を持つ場合(`git add` 後にさらに編集した場合など)は両方に表示される。

判定・色付けは `git status --porcelain` の出力を解析するだけの決定的処理で、
ローカルLLMは使わない(他のgitツール群と合わせて本プラグインに同梱している)。

## 実行手順

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/git_status_color.sh
```

出力をそのままユーザーに提示する(ANSI カラーコード付きなのでターミナルでそのまま色分けされる)。
Gitリポジトリでない場所で実行された場合は `git status` のエラーがそのまま出るので、
リポジトリのルートで実行するようユーザーに伝える。
