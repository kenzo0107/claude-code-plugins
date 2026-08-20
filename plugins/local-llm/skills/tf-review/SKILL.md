---
name: tf-review
description: Terraformの.tf差分をローカルLLM(Ollama)でMedPeer規約プレレビューする。.tf変更のcommit・push・PR作成を行う前、またはユーザーが.tfの変更に対して「プレレビュー」「規約チェック」を求めた時に使用する。クラウドLLMの利用枠を消費しない。
user-invocable: false
---

# tf-review スキル: Terraform規約プレレビュー(ローカルLLM)

`.tf` ファイルの変更を push・PR作成する前に、ローカルLLMによる規約プレレビューを実行し、
規約違反の混入を防ぐ。手動実行用の `/tf-review` コマンドと同じスクリプトを使う。

## 実行手順

### 1. 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: プレレビューをスキップし、
  その旨をユーザーに一言伝えて本来の作業を続行する(ブロッカーにしない)

### 2. レビュー実行

対象リポジトリのルートで実行する:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tf_review.py          # 未コミット変更 (HEADとの差分)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tf_review.py <base>   # 指定refとの差分
```

### 3. 指摘の扱い

- **high confidence の指摘**: 内容を確認し、実際に規約違反であれば修正してから push する。
  誤指摘(偽陽性)と判断した場合は、その理由をユーザーへの報告に含める
- **低確度の指摘**: 修正はせず、参考情報としてユーザーへの報告に含めるだけにする
- 指摘ゼロの場合も「ローカルプレレビュー: 指摘なし」と一言報告する

## 注意

- このプレレビューは補助であり、最終的な品質担保は CI (fmt / tflint / trivy / plan) が行う
- 規約ファイルは medpeer-terraform プラグインの SKILL.md を実行時参照する(スクリプト内で解決)
