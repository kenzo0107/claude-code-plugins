# aws-cost-tools Plugin

AWS Savings Plans と Reserved Instances の分析・最適化を支援するプラグインです。

## 機能

### Savings Plans 分析

AWS Cost Explorer MCPを使用して、以下の4種類のSavings Plansについて過去の使用実績を分析し、最適な割引オプションを提案します。

1. **Compute Savings Plans** - EC2、Fargate、Lambda
2. **Database Savings Plans** - Aurora、RDS、DynamoDB、ElastiCache等
3. **EC2 Instance Savings Plans** - 特定のEC2インスタンスファミリー
4. **SageMaker AI Savings Plans** - SageMakerインスタンス

### Reserved Instances (RI) 分析

現在のRI購入状況を確認し、Savings Plansとの比較分析を行います。

- EC2 Reserved Instances
- RDS Reserved Instances
- ElastiCache Reserved Nodes
- Redshift Reserved Nodes
- OpenSearch Reserved Instances

## コマンド

### `/aws-cost-tools:savings-plans-analyze`

Savings PlansとReserved Instancesの比較分析を行い、最適な割引オプションを提案します。

**使用例:**
```
/aws-cost-tools:savings-plans-analyze ~/reports/project/info.md
/aws-cost-tools:savings-plans-analyze ~/reports/project/info.md months=6
```

詳細は `commands/savings-plans-analyze.md` を参照してください。

## 必要な設定

### AWS CLI プロファイル

プラグインは `claude` という名前のAWS CLIプロファイルを使用します。

### MCP サーバー

このプラグインは以下のMCPサーバーを使用します（`.mcp.json`で自動設定）:

- `aws-ce`: AWS Cost Explorer MCP Server

## 出力

各プロジェクト、各Savings Plansタイプごとに以下を生成します：

1. **分析レポート** (Markdown形式)
   - コスト分析と推奨事項
   - Savings Plans vs RI の比較
   - 節約額の試算

2. **GitHub Issue**
   - 該当プロジェクトのTerraformリポジトリに作成
   - 購入推奨または要検討の場合のみ
