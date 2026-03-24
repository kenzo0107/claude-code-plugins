---
allowed-tools: Bash(gh pr list *), Bash(gh api *), Read
description: メトリクス(Datadog MCP or CloudWatch MCP)とterraformの実装を読んでコスト削減のIssueを作成する。
args:
- name: info_path
  description: "対象組織の info.md ファイルパス (例: ~/reports/kakari/info.md)"
  required: true
---

# コスト削減分析コマンド

プロジェクト固有情報は **`{{info_path}}`** から読み取り、記載された情報をもとにコスト削減の提案を行う。

## 手順

### 1. `{{info_path}}` の読み込み

- サービス名、AWSアカウントID、リポジトリ情報を取得する
- ファイルが存在しない場合かつ、terraformリポジトリにいる場合、terraformの実装から情報を読み取って推定していいかユーザーに尋ねる
- これもNGならエラーとして終了する

### 2. 前提条件チェック

## 重要: MCP サーバーの確認

実行前に以下の MCP サーバーが利用可能であることを確認すること:
- **AWS Cost Explorer**: 本プラグインにより `plugin:cost-reduction:aws-ce` として提供される
- **AWS CloudWatch** `plugin:cost-reduction:aws-cw` として提供される
- **GitHub**: `mcp__github__*` ツール群、または `gh` CLI
- **Datadog**（任意）: プロジェクトの `.mcp.json` で設定されている場合に利用する（info.md の Datadog Org 参照）
  - **Datadog MCP が未設定の場合**: `plugin:cost-reduction:aws-cw` (CloudWatch MCP) をメトリクス取得に使用する

#### メトリクスソースの判定

以下の順序でメトリクスソースを判定し、結果を後続の手順で利用する:

1. Datadog MCP ツール（`mcp__datadog-*` 系）が利用可能か確認する
2. **利用可能** → メトリクスソース = `datadog`
3. **利用不可** → メトリクスソース = `cloudwatch`（`plugin:cost-reduction:aws-cw` を使用）

メトリクスソースが `cloudwatch` の場合、ユーザーに以下を通知する:
> **注意: Datadog MCP が未設定のため、CloudWatch MCP を使用してメトリクスを取得します。**

#### AWS Cost Explorer MCP の確認
- AWS CE MCPツール（mcp__plugin_aws-cost-tools_aws-ce__get_cost_and_usage 等）が利用可能か確認する
- 利用できない場合は以下を表示して終了:
  > **エラー: AWS Cost Explorer MCP が未設定です。**
  > AWS CE MCP サーバーを設定し、Organization rootアカウントへのアクセスが可能な claude profile を設定してください。

### 3. 既存Issueの確認
- `{{info_path}}` に記載された各Terraformリポジトリに対して、`コスト削減` ラベルがついたIssueを検索する
  ```
  gh issue list --repo <repo> --label "コスト削減" --state all --limit 100
  ```
- open/closedの両方を確認し、特に**却下（closed で not completed）されたIssue**の理由を把握する
- 却下済みの提案と同じ内容を再提案しないようにする

### 4. AWSコスト分析（3段階の深掘り）

各AWSアカウントのprd環境について、以下の3段階で深掘りする。
表面的なサービス別コストで止めず、具体的な原因と対応策が見えるレベルまで掘り下げること。

#### Level 1: サービス別コスト
- aws-ce MCPを使い、先月と先々月のサービス別コストを比較する
- コストが高い順に把握し、増減の大きいサービスを特定する
- **上位サービス（目安: $50/月以上）を Level 2 の対象とする**

#### Level 2: 使用タイプ別コスト
- Level 1 で特定した各サービスについて、`USAGE_TYPE` で分解する
  ```
  filter: SERVICE = "<対象サービス>", group_by: USAGE_TYPE
  ```
- 例: Datadog → MetricMonitorUsage / GMD-Metrics / DataProcessing-Bytes 等
- **コスト割合が大きい使用タイプ（目安: $20/月以上）を Level 3 の対象とする**

#### Level 3: 使用タイプごとの原因特定
- 使用タイプに応じたAWS CLIコマンドで実態を調査する
- 以下は主要な使用タイプと対応する調査コマンドの例:

| 使用タイプ | 調査内容 | コマンド例 |
|---|---|---|
| DataProcessing-Bytes (ログ取込) | ロググループ別の保存容量 | `aws logs describe-log-groups --query 'logGroups[].{name:logGroupName, storedBytes:storedBytes}'` |
| MetricMonitorUsage (カスタムメトリクス) | ネームスペース別メトリクス数 | `aws cloudwatch list-metrics` をネームスペース別に集計 |
| GMD-Metrics (GetMetricData) | 日次コスト推移、ポーリング元の特定 | CE で DAILY granularity、Datadog統合設定との突合 |
| MetricStreamUsage | ストリーム設定の確認 | Terraform の metric_stream リソースを確認 |
| NatGateway-Bytes | NAT Gateway 別のデータ転送量 | `aws ec2 describe-nat-gateways` + CloudWatch NATGateway メトリクス |
| TimedStorage-ByteHrs (ログ保存) | ロググループ別の保存量と保持期間 | `aws logs describe-log-groups` |

- **保存量から月間取り込み量を推定する場合**: 推定月間取込量 = storedBytes / 保持日数 × 30
- ロググループが大きい場合は、ストリームプレフィックス別の構成も確認する（コンテナ種別の特定）
- Lambda@Edge 等クロスリージョンにログが分散するサービスは、主要リージョンも確認する

### 5. メトリクス分析

`{{info_path}}` に記載されたサービスについて、Step 2 で判定したメトリクスソースに基づき以下を調査する。

#### メトリクスソースが `datadog` の場合

Datadog MCP を使用して以下を調査する:
- リソース使用率（CPU、メモリ等）が低いサービスやホスト
- スケーリング設定に対して実使用率が低いもの
- ログの量が過剰なサービス
- 不要なモニターやダッシュボード

#### メトリクスソースが `cloudwatch` の場合

AWS CloudWatch MCP (`plugin:cost-reduction:aws-cw`) を使用して以下を調査する:

- **ECS / EC2 リソース使用率**:
  - `AWS/ECS` ネームスペース: `CPUUtilization`, `MemoryUtilization` をサービス別に取得
  - `AWS/EC2` ネームスペース: `CPUUtilization`, `MemoryUtilization` をインスタンス別に取得
  - 直近1週間の平均・最大値を確認し、ピーク時でも使用率が低い（目安: 平均 30% 以下）リソースを特定する
- **RDS / ElastiCache リソース使用率**:
  - `AWS/RDS` ネームスペース: `CPUUtilization`, `FreeableMemory`, `DatabaseConnections`
  - `AWS/ElastiCache` ネームスペース: `CPUUtilization`, `DatabaseMemoryUsagePercentage`
  - 過剰スペックのインスタンスを特定する
- **Auto Scaling / ECS スケーリング効率**:
  - `AWS/AutoScaling` ネームスペース: `GroupDesiredCapacity`, `GroupInServiceInstances`
  - ECS サービスの `desiredCount` と `runningCount` の推移
  - スケーリング設定に対して実使用率が低い構成を特定する
- **Lambda 実行効率**:
  - `AWS/Lambda` ネームスペース: `Duration`, `MemorySize`, `Invocations`
  - メモリ割り当てに対して実使用量が少ない関数を特定する
- **NAT Gateway / データ転送**:
  - `AWS/NATGateway` ネームスペース: `BytesOutToDestination`, `BytesOutToSource`
  - 転送量が多いゲートウェイを特定する

### 6. Terraform実装の確認
- `{{info_path}}` に記載されたTerraformリポジトリを `ghq root` で取得したパスから読み込む
  ```
  ghq list --full-path | grep <repo-name>
  ```
- 以下の観点でコスト削減の余地を分析する:
  - 過剰なインスタンスサイズ（RDS, ElastiCache, ECS等）
  - 不要なリソース（使われていないEIP, NAT Gateway, ロードバランサー等）
  - リザーブドインスタンスやSavings Plansの適用余地
  - ストレージの最適化（S3ライフサイクル、EBSボリュームタイプ等）
  - ログ保持期間の最適化（CloudWatch Logs等）
  - 不要なデータ転送コスト

### 7. 分析結果の提示
- 分析結果をまとめ、コスト削減の提案を一覧で提示する
- 各提案には以下を含める:
  - **対象リソース**: 何を変更するか
  - **現状**: 現在のコスト・設定
  - **提案内容**: 具体的な変更内容
  - **削減予想額**: 月額でどれくらい削減できるか
  - **副作用・リスク**: パフォーマンス影響等があれば明記
- 既存の却下済みIssueと重複する提案がある場合はその旨を明示する

### 8. Issue作成
- ユーザーに提案内容を提示し、Issue作成の承認を求める
- 追加調査の指示があれば対応する
- 承認された提案について、対応するTerraformリポジトリにIssueを作成する:
  ```
  gh issue create --repo <terraform-repo> --title "<提案タイトル>" --label "コスト削減" --body "<本文>"
  ```
- Issueの本文には以下を含める:
  - 背景（コスト分析の結果）
  - 提案内容の詳細
  - 削減予想額（月額）
  - 副作用・リスク（ある場合）
  - 参考情報（Datadogのメトリクス、AWSコストデータ等）
