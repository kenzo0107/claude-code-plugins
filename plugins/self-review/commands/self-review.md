---
allowed-tools: Bash(git *), Bash(gh *), Bash(ghq list*), Read, Grep, Glob
description: PR作成前に自分のコミット(ブランチ差分)をセルフレビューする。蓄積したレビュー知見を照合
user-invocable: true
args:
  - name: base
    description: "比較先のベースブランチ (例: origin/develop)。省略時は origin のHEADブランチを自動判定"
    required: false
---

# self-review: PR作成前のセルフレビュー

`${CLAUDE_PLUGIN_ROOT}/skills/self-review/SKILL.md` を読み、その手順に従って
現在のブランチのセルフレビューを実行する。

- ベースブランチ: `$ARGUMENTS` が指定されていればそれを使う。省略時はSKILL.mdの手順で自動判定する
- 蓄積知見(learnings)の照合を必ず行い、照合した知見の件数を報告に含める
- 指摘の修正はユーザーが明示的に依頼した場合のみ行う
