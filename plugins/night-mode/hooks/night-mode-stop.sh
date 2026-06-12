#!/bin/bash
# Night Mode: セッション終了時にフラグ削除 & macOS 通知を送る (Stop hook)

FLAG="$HOME/.claude/night-mode-active"
[ ! -f "$FLAG" ] && exit 0

# フラグ削除 (通常モードに戻す)
rm -f "$FLAG"

# ログファイルのパス
LOG_FILE="$HOME/.claude/night-mode-log-$(date +%Y%m%d).txt"
LOG_LINE_COUNT=0
if [ -f "$LOG_FILE" ]; then
  LOG_LINE_COUNT=$(wc -l < "$LOG_FILE" | tr -d ' ')
fi

# macOS 通知
osascript -e "display notification \"実行コマンド数: ${LOG_LINE_COUNT}件 | ログ: ${LOG_FILE}\" with title \"🌙 Night Mode 終了\" subtitle \"Claude Code 夜間作業が完了しました\"" 2>/dev/null

exit 0
