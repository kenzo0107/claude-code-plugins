---
allowed-tools: Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*), Bash(gh pr view *), Bash(gh pr diff *), Bash(gh pr review *), Bash(gh pr comment *), Read
description: 他人のPRをローカルLLMでプレレビューし、レビューコメント案を作る(クラウド利用枠を消費しない)
user-invocable: true
args:
  - name: pr
    description: "PR番号またはURL。--repo owner/repo でカレント以外のリポジトリも指定可"
    required: true
---

# pr-review: 他人のPRのプレレビュー(ローカルLLM)

`gh pr diff` で取得した差分を、拡張子ごとのセキュリティ観点(Go/Python/Ruby/Kotlin/TypeScript)と
一般品質観点でローカルLLM(Ollama)がレビューし、レビューコメント案を Markdown で出す。
投稿はユーザーが確認してから行う。

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない場合: Ollamaが起動していない。`brew services start ollama` を案内して終了する
- モデル一覧に `gemma4:12b` が無い場合: `ollama pull gemma4:12b` を案内して終了する
- `gh auth status` が未認証なら案内して終了する

### ステップ2: レビュー実行

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pr_review.py $ARGUMENTS
```

差分が大きい場合はファイル単位に分割してレビューするため数分かかることがある。

### ステップ3: 結果の提示

- スクリプトの Markdown 出力をそのまま提示する(自分の言葉で書き直さない)
- 「参考(low)」は偽陽性の可能性があることを明記する
- 自分(Claude)で指摘の妥当性を再検証・追加レビューはしない。ユーザーが明示的に依頼した場合のみ対応する

### ステップ4: 投稿(ユーザーが承認した場合のみ)

ユーザーが「投稿して」と明示した場合のみ、承認した内容で投稿する。未承認のまま投稿しない。

```bash
gh pr review <番号> --comment --body "<承認された内容>"
```

## 注意

- 見逃しなく確認したい重要なPRでは `LOCAL_REVIEW_MODEL=qwen3.6:27b` を指定する(数倍遅い)
- 決定的ツール(linter / SAST)の代替ではなく、文脈判断の補助
