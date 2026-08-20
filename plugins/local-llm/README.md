# local-llm

ローカルLLM(Ollama)でクラウドLLMの利用枠を消費せずに定型作業を行うプラグイン。

## 前提

- [Ollama](https://ollama.com/) 0.32以降: `brew install ollama && brew services start ollama`
- モデル: `ollama pull gemma4:12b`(約8GB。メモリ16GB以上のMac推奨)

## コマンド

### /tf-review [base]

カレントのTerraformリポジトリの `.tf` 差分を、MedPeerコーディング規約
(medpeer-terraformプラグインのSKILL.md)に照らしてローカルLLMがプレレビューする。

```
/tf-review                # 未コミットの変更 (HEADとの差分)
/tf-review origin/main    # 指定refとの差分
```

- push前のセルフチェック用。何度実行してもクラウド利用枠を消費しない
- 指摘は参考情報(偽陽性あり得る)。最終判断は人間とCI(fmt/tflint/trivy)が担う
- モデル変更: 環境変数 `TF_REVIEW_MODEL`(既定: gemma4:12b)

## 設計方針

制御フローはスクリプトで固定し、判断が必要な箇所だけローカルLLMを呼ぶ。
LLMの出力は機械検証(マスク漏れ再走査など)で品質を担保する。
