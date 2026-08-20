---
name: pr-body
description: gh pr create でPRを作成する場面で、ブランチ差分からローカルLLM(Ollama)でPR本文(Summary/Test plan)を生成する。ユーザーからPR作成を依頼された時に使用する。クラウドLLMの利用枠を消費しない。
user-invocable: false
---

# pr-body スキル: PR本文生成(ローカルLLM)

PR本文(Summary/Test plan)を自分(Claude)の推論で組み立てる代わりに、ローカルLLMに生成させる。

## 実行手順

### 1. 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: このスキルをスキップし、その旨をユーザーに
  一言伝えて通常通り自分でPR本文を作成する(ブロッカーにしない)

### 2. base ref特定

現在のブランチがデフォルトブランチから分岐した時点との差分を見るため、`origin/<デフォルトブランチ>`
(通常 `origin/main`)を base とする。

### 3. 生成

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pr_body.py <base>
```

### 4. 採用

- 生成結果(Summary/Test plan)がdiffの内容と明らかに食い違っていないか目視で確認する
  (誤りがあれば自分で修正してよい)
- 問題なければそのまま `gh pr create --body "<生成結果>"` に使う。自分の言葉で本文を新たに
  書き直さない(それではローカルLLMを使う意味がなくなる)
- PRタイトルは短く安価なので、これまで通り自分で簡潔に作成してよい

## 注意

- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b)
