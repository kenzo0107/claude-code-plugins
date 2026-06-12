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

# クラウド CLI 全般 (gcloud / az / doctl / heroku / firebase / vercel / netlify / pulumi / serverless)
if echo "$CMD" | grep -qiE '^\s*(gcloud|gsutil|bq|az|doctl|heroku|firebase|vercel|netlify|pulumi|serverless|sls)\s'; then
  block "クラウド CLI コマンドをブロックしました (SaaS リソースの作成・更新・削除を防止): $CMD"
fi

# Kubernetes / Helm (リソース変更系サブコマンドのみ)
if echo "$CMD" | grep -qiE '^\s*kubectl\s+(apply|create|delete|patch|edit|replace|scale|rollout|exec|cp|drain|cordon|uncordon|taint|label|annotate|set)\b'; then
  block "kubectl の変更系操作をブロックしました: $CMD"
fi
if echo "$CMD" | grep -qiE '^\s*helm\s+(install|upgrade|uninstall|rollback|delete|push)\b'; then
  block "helm の変更系操作をブロックしました: $CMD"
fi

# GitHub CLI (リポジトリ / PR / Issue / Release / Workflow の変更操作)
if echo "$CMD" | grep -qiE '^\s*gh\s+(repo\s+(create|delete|edit|archive|rename|transfer|fork)|pr\s+(create|close|merge|edit|comment|review|reopen|ready)|issue\s+(create|close|edit|comment|reopen|delete|transfer|pin|unpin)|release\s+(create|delete|edit|upload)|workflow\s+(run|enable|disable)|secret\s+(set|delete)|variable\s+(set|delete)|api\s+.*-X\s*(POST|PUT|PATCH|DELETE))'; then
  block "gh の変更系操作をブロックしました: $CMD"
fi

# パッケージレジストリへの公開
if echo "$CMD" | grep -qiE '^\s*(npm\s+(publish|unpublish)|yarn\s+publish|pnpm\s+publish|cargo\s+publish|gem\s+push|twine\s+upload|poetry\s+publish)'; then
  block "パッケージ公開コマンドをブロックしました: $CMD"
fi

# Docker レジストリ Push (リモートイメージ変更)
if echo "$CMD" | grep -qiE '^\s*docker\s+(push|image\s+push|manifest\s+push)\b'; then
  block "docker push をブロックしました (リモートレジストリへの変更を防止): $CMD"
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
