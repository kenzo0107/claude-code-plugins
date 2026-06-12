#!/bin/bash
# Night Mode: 危険な Bash コマンドをブロックする (PreToolUse hook)
# フラグファイルが存在する間のみ有効

FLAG="$HOME/.claude/night-mode-active"
[ ! -f "$FLAG" ] && exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

block() {
  echo "{\"decision\": \"block\", \"reason\": \"🌙 Night Mode: $1\"}" >&2
  exit 2
}

# ファイルシステム破壊: rm -rf でシステム・ホーム・カレントディレクトリ全削除
if echo "$CMD" | grep -qiE 'rm\s+(-[rRfF]+\s+)*(-[rRfF]+\s+)*(\/\s*$|~\/?\s*$|\$HOME\/?\s*$|\.\s*$|\.\/$|\/\*)'; then
  block "破壊的な rm 操作をブロックしました (rm -rf / や rm -rf ~ など)"
fi

# Git force push (履歴改ざん)
if echo "$CMD" | grep -qiE 'git\s+push\s+.*(--force|-f)(\s|$)'; then
  block "git force push をブロックしました"
fi

# git reset --hard (未コミット変更の消失)
if echo "$CMD" | grep -qiE 'git\s+reset\s+--hard'; then
  block "git reset --hard をブロックしました"
fi

# デプロイ操作 (terraform / cdk / sam / aws)
if echo "$CMD" | grep -qiE '^\s*(terraform\s+(apply|destroy)|cdk\s+deploy|sam\s+deploy|aws\s+)'; then
  block "デプロイ・クラウド操作コマンドをブロックしました: $CMD"
fi

# インタラクティブコマンド (無人実行でハング)
if echo "$CMD" | grep -qiE '^\s*(vi|vim|nvim|nano|emacs|less|more|man)\s'; then
  block "インタラクティブコマンドをブロックしました (夜間無人実行ではハングします)"
fi

# プロセス強制終了 (システム影響リスク)
if echo "$CMD" | grep -qiE '(pkill\s+-9|killall\s+)'; then
  block "強制プロセス終了コマンドをブロックしました"
fi

exit 0
