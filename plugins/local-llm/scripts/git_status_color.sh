#!/usr/bin/env bash
# git status をステージ済み(緑)/未ステージ・未追跡(赤)に色分けして表示する。
# 1ファイルがステージ済みかつ未ステージの変更も持つ場合(例: git add 後にさらに編集した場合)は
# 両方のセクションに表示する(通常の `git status` の長形式表示と同じ扱い)。
#
# 使い方:
#   git_status_color.sh
set -euo pipefail

GREEN='\033[32m'
RED='\033[31m'
BOLD='\033[1m'
RESET='\033[0m'

staged=()
unstaged=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  xy="${line:0:2}"
  path="${line:3}"

  if [ "$xy" = "??" ]; then
    unstaged+=("${path} (untracked)")
    continue
  fi

  x="${xy:0:1}"
  y="${xy:1:1}"
  [ "$x" != " " ] && staged+=("$path")
  [ "$y" != " " ] && unstaged+=("$path")
done < <(git status --porcelain=v1 --untracked-files=all)

echo -e "${BOLD}ステージ済み (staged)${RESET}"
if [ ${#staged[@]} -eq 0 ]; then
  echo "  (なし)"
else
  for f in "${staged[@]}"; do
    echo -e "  ${GREEN}${f}${RESET}"
  done
fi

echo
echo -e "${BOLD}未ステージ・未追跡 (not staged)${RESET}"
if [ ${#unstaged[@]} -eq 0 ]; then
  echo "  (なし)"
else
  for f in "${unstaged[@]}"; do
    echo -e "  ${RED}${f}${RESET}"
  done
fi
