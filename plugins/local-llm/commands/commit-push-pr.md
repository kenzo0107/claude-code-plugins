---
allowed-tools: Bash(git status:*), Bash(git branch:*), Bash(git checkout:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(gh pr create:*), Bash(gh repo view:*), Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*)
description: ブランチ作成・コミット・push・PR作成を一括で行う。メッセージ生成はローカルLLM(公式のcommit-commands:commit-push-prと同等の作業をクラウド利用枠を消費せず実施)
user-invocable: true
---

# commit-push-pr: コミット→push→PR作成(ローカルLLM)

`commit-commands:commit-push-pr` と同じ一連の作業(ブランチ作成・コミット・push・PR作成)を、
コミットメッセージとPR本文の生成にローカルLLM(Ollama)を使って行う。
`commit-commands:commit-push-pr` はコマンド自身の `allowed-tools` が git/gh 系のみに絞られており
python3/curlを呼べないため、ローカルLLMのスキルが発火できない。このコマンドはその制約を受けずに
同等の結果をクラウド利用枠ゼロで得るためのもの。

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `qwen3.6:27b` / `gemma4:12b` のいずれかが無い場合: その旨を伝え、通常の
  `commit-commands:commit-push-pr` 相当の手順(自分でメッセージ・本文を作成)にフォールバックする

### ステップ2: ブランチ

`main`(または `master`)上にいる場合は、変更内容に応じた名前で新しいブランチを作成する。

### ステップ3: コミット

```bash
git add <関連ファイル>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/commit_msg.py
```

生成結果をそのまま使って `git commit -m "<メッセージ>"` する(自分の言葉で書き直さない)。

### ステップ4: push

```bash
git push -u origin <ブランチ名>
```

### ステップ5: PR作成

デフォルトブランチ(`gh repo view --json defaultBranchRef` 等で特定)を base とする:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pr_body.py origin/<デフォルトブランチ>
```

生成結果をそのまま `gh pr create --title "<簡潔なタイトル>" --body "<生成結果>"` に使う
(本文は書き直さない。タイトルは短く安価なので自分で作成してよい)。

### ステップ6: 結果報告

作成したPRのURLを提示する。

## 注意

- コミットメッセージ生成(`commit_msg.py`)は既定で `qwen3.6:27b` を使う(精度検証の結果、
  `gemma4:12b` は複数の変更を含むdiffで箇条書きへの分解を誤ることがあったため)。
  PR本文生成(`pr_body.py`)は既定 `gemma4:12b` のままで十分な精度
- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`(両スクリプト共通)
- `gh` のインストール・認証が前提(未認証ならその旨を案内して終了する)
