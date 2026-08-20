---
allowed-tools: Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*), Read
description: Terraform差分をローカルLLMでMedPeer規約プレレビューする(クラウド利用枠を消費しない)
user-invocable: true
args:
  - name: base
    description: "比較先のgit ref (例: origin/main)。省略時は HEAD (未コミットの変更)"
    required: false
---

# tf-review: Terraform規約プレレビュー(ローカルLLM)

カレントディレクトリのTerraformリポジトリの `.tf` 差分を、ローカルLLM(Ollama)で
MedPeerコーディング規約に照らしてプレレビューする。処理はすべてローカルで完結し、
クラウドLLMの利用枠を消費しない。

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない場合: Ollamaが起動していない。`brew services start ollama` を案内して終了する
- モデル一覧に `gemma4:12b` が無い場合: `ollama pull gemma4:12b` を案内して終了する

### ステップ2: レビュー実行

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tf_review.py $ARGUMENTS
```

- 引数(`$ARGUMENTS`)が指定されていればそのrefとの差分、なければHEADとの差分(未コミット変更)をレビューする
- 実行時間はdiffの規模により数十秒〜数分かかる

### ステップ3: 結果の提示

- スクリプトの出力(指摘一覧)をそのまま提示する
- 「低確度」と付いた指摘は偽陽性の可能性があることを明記する
- 自分(Claude)で指摘の妥当性を検証・修正はしない。これはローカルLLMによるプレレビューであり、
  クラウド利用枠の節約が目的。ユーザーが修正を明示的に依頼した場合のみ対応する

## 注意

- 規約ファイルは medpeer-terraform プラグインの SKILL.md を実行時に参照する。
  見つからない場合はスクリプトがエラーメッセージでパスを案内する
- モデルは環境変数 `TF_REVIEW_MODEL` で変更可能(既定: gemma4:12b)
