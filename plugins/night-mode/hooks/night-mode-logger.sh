#!/bin/bash
# Night Mode: 実行された Bash コマンドをログファイルに記録する (PostToolUse hook)
# フラグファイルが存在する間のみ有効

FLAG="$HOME/.claude/night-mode-active"
[ ! -f "$FLAG" ] && exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
[ -z "$CMD" ] && exit 0

LOG_FILE="$HOME/.claude/night-mode-log-$(date +%Y%m%d).txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] $CMD" >> "$LOG_FILE"

exit 0
