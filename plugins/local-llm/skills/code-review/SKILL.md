---
name: code-review
description: Go/Python/Ruby/Kotlin/TypeScriptのコード差分をローカルLLM(Ollama)でセキュリティ・品質のプレレビューする。.go/.py/.rb/.kt/.tsの変更をcommit・push・PR作成する前、またはユーザーが「プレレビュー」「セキュリティチェック」を求めた時に使用する。クラウドLLMの利用枠を消費しない。
user-invocable: false
---

# code-review スキル: コードプレレビュー(ローカルLLM)

`.go` / `.py` / `.rb` / `.kt` / `.ts` などの変更を push・PR作成する前に、ローカルLLMによるセキュリティ・品質プレレビューを
実行し、明らかな問題の混入を防ぐ。手動実行用の `/code-review` コマンドと同じスクリプトを使う。

## 実行手順

### 1. 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: プレレビューをスキップし、その旨をユーザーへ
  一言伝えて本来の作業を続行する(ブロッカーにしない)

### 2. 対象言語の判定

差分(未コミット、またはこれからコミットしようとしている範囲)に対応言語(`.go` `.py` `.rb` `.kt` `.ts/.tsx/.js`)が含まれるか確認する。

### 3. レビュー実行

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/code_review.py --auto
```

`--auto` は差分に含まれる拡張子から観点ファイル(`rules/go-security.md`, `python-security.md`, `ruby-security.md`,
`kotlin-android.md`, `typescript-security.md`)を自動選択し、該当言語のファイルだけをそれぞれレビューする。
特定の観点だけ使いたい場合は `code_review.py <rules.md> [base]` と明示する。


### 4. 指摘の扱い

- **high confidence の指摘**: 内容を確認し、実際に問題であれば修正してから push する。
  誤指摘(偽陽性)と判断した場合は、その理由をユーザーへの報告に含める
- **低確度の指摘**: 修正はせず、参考情報としてユーザーへの報告に含めるだけにする
- 指摘ゼロの場合も「ローカルプレレビュー: 指摘なし」と一言報告する

## 精度の目安(evals で継続測定。最新は local-llm リポジトリの evals/RESULTS.md)

意図的に7件の脆弱性を仕込んだPythonサンプルで検証: `gemma4:12b` は6/7件検出(パストラバーサルを
見逃し、約60秒)、`qwen3.6:27b` は7/7件検出(約2分30秒)。誤検知なし。セキュリティ影響が大きそうな
差分では `LOCAL_REVIEW_MODEL=qwen3.6:27b` を使う判断をしてよい。

## 注意

- このプレレビューは補助であり、最終的な品質担保はCI(linter/セキュリティスキャナ等)が行う
- gosec / govulncheck / ruff 等の決定的ツールの代替ではない
