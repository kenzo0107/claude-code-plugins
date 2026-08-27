# レビュー知見: terraform

フォーマットは `README.md` を参照。`/learn-review` が追記する。

<!-- ここから下にエントリを追記する -->

## TF-001: IAMポリシーのResource指定はアクションのリソースレベル対応を確認する
- 分類: security
- 登録日: 2026-08-24
- 出典: medpeer-dev/peerx-id-terraform PR #304

IAMアクションにはリソースレベルの制限に対応していないもの(例: `logs:StopQuery` は `*` のみ)や、
指定できるARN形式が限られるもの(例: `kms:Decrypt` はキーARNのみでエイリアスARN不可)がある。
対応していないARNを書くと権限が黙って効かず、実行時に初めて失敗する。ポリシー作成時は
AWSのService Authorization Referenceで各アクションのリソースタイプ対応を確認する。

## TF-002: variableの型はobject()と optional()で詳細に定義する
- 分類: design
- 登録日: 2026-08-24
- 出典: medpeer-dev/peerx-id-terraform PR #304

`map(any)` などの緩い型ではせっかくvariableを通しても型検査が機能せず、キーのtypoや
構造の誤りがplan時に検出できない。`object()` でスキーマを細かく指定し、
省略可能な属性には `optional()` を使う。

悪い例:
```hcl
variable "alarm_config" {
  type = map(any)
}
```

良い例:
```hcl
variable "alarm_config" {
  type = object({
    name          = string
    slack_channel = string
    enabled       = optional(bool, true)
  })
}
```

## TF-003: required_versionは使用している機能の最低バージョンに正確に合わせる
- 分類: correctness
- 登録日: 2026-08-24
- 出典: medpeer-dev/peerx-id-terraform PR #304

実際に使っている言語機能が要求するバージョンより低い `required_version` を書くと、
古いTerraformでplanが通らず初めて発覚する。使用機能の導入バージョン
(例: ephemeral variableは1.10、write-only attributeは1.11)を確認して正確に指定する。

## TF-004: EventBridge経由の非同期起動にはリトライ設定とDLQを付ける
- 分類: operations
- 登録日: 2026-08-24
- 出典: medpeer-dev/peerx-id-terraform PR #304

EventBridgeターゲット(Lambda等)にretry_policyやDLQ(dead_letter_config)がないと、
起動失敗したイベントが消失し、どのイベントで失敗したのか追跡できない。
`aws_cloudwatch_event_target` には `retry_policy` と `dead_letter_config` を設定する。

## TF-005: ハードコードした外部識別子はdataソースを通して存在検証する
- 分類: design
- 登録日: 2026-08-24
- 出典: medpeer-dev/peerx-id-terraform PR #304

モデルIDやAMI IDなどの外部サービス識別子を文字列でハードコードすると、
存在しない・利用不可の識別子でもplanが通り、実行時に初めて失敗する。
対応するdataソース(例: `data.aws_bedrock_foundation_model`)を通すことで
plan時に存在を検証でき、可読性も保てる。

## TF-006: S3の非現行バージョン保持期間は復旧要件から決める
- 分類: operations
- 登録日: 2026-08-24
- 出典: medpeer-dev/data-platform-terraform PR #1422

バージョニング有効バケットの `noncurrent_version_expiration` を短くしすぎると、
誤削除・誤上書きに気づいたときには非現行バージョンが消えていて復旧できない。
サービスが直接参照しないバケットなら7日程度が目安。コスト削減だけでなく
「何日以内なら復旧が必要か」を基準に決める。
