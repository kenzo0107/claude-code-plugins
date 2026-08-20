---
allowed-tools: Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*), Bash(git diff *), Read
description: Go/Pythonのコード差分をセキュリティ・品質観点でローカルLLMがプレレビューする(クラウド利用枠を消費しない)
user-invocable: true
args:
  - name: base
    description: "比較先のgit ref (例: origin/main)。省略時は HEAD (未コミットの変更)"
    required: false
---

# code-review: コードプレレビュー(ローカルLLM)

カレントディレクトリのリポジトリの差分を、ローカルLLM(Ollama)でセキュリティ・品質観点から
プレレビューする。処理はすべてローカルで完結し、クラウドLLMの利用枠を消費しない。

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない場合: Ollamaが起動していない。`brew services start ollama` を案内して終了する
- モデル一覧に `gemma4:12b` が無い場合: `ollama pull gemma4:12b` を案内して終了する

### ステップ2: 対象言語の判定

`git diff $ARGUMENTS --stat` (省略時は `git diff --stat`) を見て、`.go` / `.py` の変更有無を確認する。
両方含まれる場合は両方の観点で実行する。どちらも無ければ「対象言語(Go/Python)の差分なし」と伝えて終了する。

### ステップ3: レビュー実行

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/code_review.py ${CLAUDE_PLUGIN_ROOT}/rules/go-security.md $ARGUMENTS
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/code_review.py ${CLAUDE_PLUGIN_ROOT}/rules/python-security.md $ARGUMENTS
```

該当する言語の方だけ実行する。

### ステップ4: 結果の提示

- スクリプトの出力(指摘一覧)をそのまま提示する
- 「低確度」の指摘は偽陽性の可能性があることを明記する
- 自分(Claude)で指摘の妥当性を検証・修正はしない。ユーザーが修正を明示的に依頼した場合のみ対応する

## 精度の目安(検証済み)

意図的に7件の脆弱性を仕込んだPythonサンプルで検証: `gemma4:12b` は6/7件検出(パストラバーサルを
見逃し、約60秒)、`qwen3.6:27b` は7/7件検出(約2分30秒)。誤検知なし。見逃しなく確認したい重要な
差分では `LOCAL_REVIEW_MODEL=qwen3.6:27b` を指定する。

## 注意

- gosec / govulncheck / ruff 等の決定的ツールの代替ではない。文脈判断の補助
- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b)
