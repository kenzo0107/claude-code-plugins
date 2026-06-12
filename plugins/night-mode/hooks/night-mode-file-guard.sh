#!/bin/bash
# Night Mode: 機密ファイルの Edit/Write をブロックする (PreToolUse hook)
# フラグファイルが存在する間のみ有効

FLAG="$HOME/.claude/night-mode-active"
[ ! -f "$FLAG" ] && exit 0

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# ホームディレクトリの ~ を展開
FILE="${FILE/#\~/$HOME}"

block() {
  echo "{\"decision\": \"block\", \"reason\": \"🌙 Night Mode: 機密ファイルの編集をブロックしました ($FILE)\"}" >&2
  exit 2
}

# SSH 秘密鍵・設定
if echo "$FILE" | grep -qE "^$HOME/\.ssh/"; then
  block
fi

# AWS 認証情報
if echo "$FILE" | grep -qE "^$HOME/\.aws/(credentials|config)$"; then
  block
fi

# シェル設定
if echo "$FILE" | grep -qE "^$HOME/\.(zshrc|bashrc|bash_profile|profile|zprofile|zshenv)$"; then
  block
fi

# Git グローバル設定
if echo "$FILE" | grep -qE "^$HOME/\.gitconfig$"; then
  block
fi

# システムファイル
if echo "$FILE" | grep -qE "^/etc/"; then
  block
fi

# 秘密鍵・証明書ファイル
if echo "$FILE" | grep -qiE "\.(pem|key|p12|pfx|cer|crt)$"; then
  block
fi

# .env ファイル (ルート直下またはホーム直下)
if echo "$FILE" | grep -qE "^$HOME/[^/]*\.env$|^$HOME/[^/]*/[^/]*\.env$"; then
  block
fi

exit 0
