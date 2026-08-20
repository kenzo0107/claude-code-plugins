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

### /commit-msg

ステージ済みの変更(`git add` 済み)からコミットメッセージをローカルLLMで生成する。

### /pr-body [base]

ブランチ差分からGitHub PRの本文(Summary/Test plan)をローカルLLMで生成する。

```
/pr-body                # デフォルトブランチとの差分
/pr-body origin/main    # 指定refとの差分
```

### /code-review [base]

Go/Pythonのコード差分をセキュリティ・品質観点でローカルLLMがプレレビューする。
同梱観点: `rules/go-security.md`、`rules/python-security.md`。
意図的に7件の脆弱性を仕込んだPythonサンプルでの検証では、`gemma4:12b` が6/7件検出
(約60秒)、`qwen3.6:27b` が7/7件検出(約2分30秒)、誤検知なし。

### /commit-push-pr

ブランチ作成・コミット・push・PR作成を一括で行う。公式 `commit-commands:commit-push-pr`
と同等の作業を、メッセージ・本文の生成にローカルLLMを使って行う版。

> **公式 `commit-commands:commit` / `commit-commands:commit-push-pr` との違い**:
> 公式コマンドは `allowed-tools` が git/gh 系のみに絞られており、プロンプトも
> 「他のツールは使うな」と明記しているため、本プラグインの自動発火スキル
> (`python3` / `curl` が必要)はその実行中には発火できない。同等の作業をローカルLLMで
> 行いたい場合は、公式コマンドではなく `/commit-msg`(= `/commit` 相当)や
> `/commit-push-pr`(= `/commit-push-pr` 相当)をこちらのプラグインから使うこと。

## 自動発火するスキル

`/tf-review` `/commit-msg` `/pr-body` `/code-review` は、対応する場面
(Terraform差分のレビュー・コミット作成・PR作成・Go/Pythonの差分レビュー)で
Claude Codeが自律的に判断してスキルとしても呼び出す(`user-invocable: false`)。
Ollamaが起動していない場合はスキップされ、通常のクラウドLLMでの処理にフォールバックする
(ブロッカーにはしない)。

- モデル変更: いずれも環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b。tf-reviewのみ
  `TF_REVIEW_MODEL`)

## 設計方針

制御フローはスクリプトで固定し、判断が必要な箇所だけローカルLLMを呼ぶ。
LLMの出力は機械検証(マスク漏れ再走査など)や人間の最終確認で品質を担保する。
生成系(コミットメッセージ・PR本文)は「ローカルLLMの出力をそのまま使う」ことが目的なので、
Claudeが結果を自分の言葉で書き直すことはしない。
