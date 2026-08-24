---
allowed-tools: Bash(git *), Bash(gh *), Bash(ghq list*), Read, Write, Edit, Grep, Glob
description: PRで受けたレビューコメントを一般化してself-reviewの知見(learnings)に蓄積する
user-invocable: true
args:
  - name: pr
    description: "対象のPR番号またはURL。省略時は現在のブランチのPRを対象にする"
    required: false
---

# learn-review: 受けたレビューを知見として蓄積する

`${CLAUDE_PLUGIN_ROOT}/skills/learn-review/SKILL.md` を読み、その手順に従って
レビューコメントの収集・選別・一般化・マスキング・追記を実行する。

- 対象PR: `$ARGUMENTS` が指定されていればそれを、省略時は現在のブランチのPRを使う
- 知見化する候補は追記前に必ずユーザーに提示し、承認を得てから書き込む
- 書き込み先はプラグインキャッシュではなくソースリポジトリ(SKILL.mdの手順で特定)
