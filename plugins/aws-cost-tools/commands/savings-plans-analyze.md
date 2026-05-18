# コマンド仕様書: /savings-plans-analyze

## 目的
Savings Plans の購入および利用状況を分析し、推奨事項を提供する

## パラメータ

### 必須パラメータ
なし

### オプションパラメータ
- `--lookback-period`: 分析期間（デフォルト: 30日）
  - 値: `7`, `30`, `60`, `90`
- `--payment-option`: 支払いオプションでフィルタ
  - 値: `NO_UPFRONT`, `PARTIAL_UPFRONT`, `ALL_UPFRONT`
- `--term`: 契約期間でフィルタ
  - 値: `ONE_YEAR`, `THREE_YEARS`

## 実行フロー

1. 現在の Savings Plans 契約状況を取得
   - AWS Cost Explorer API を使用して既存の Savings Plans を取得

2. Savings Plans の利用率と適用範囲を分析
   - 指定された期間の利用率データを取得
   - 適用範囲（カバレッジ）を算出

3. Savings Plans 推奨事項を取得
   - Cost Explorer の推奨 API を使用
   - 指定された支払いオプションと期間でフィルタ

4. 結果を構造化して返却
   - 現在の契約情報
   - 利用状況の分析
   - コスト削減の推奨事項

## 出力形式

```json
{
  "current_commitments": {
    "active_plans": [
      {
        "id": "string",
        "type": "COMPUTE_SP | EC2_INSTANCE_SP",
        "commitment": "number",
        "start_date": "string",
        "end_date": "string",
        "payment_option": "string",
        "term": "string"
      }
    ],
    "total_commitment": "number"
  },
  "utilization": {
    "period": "string",
    "average_utilization": "number",
    "total_commitment_hours": "number",
    "used_commitment_hours": "number",
    "unused_commitment_hours": "number",
    "on_demand_cost": "number",
    "savings_plans_cost": "number",
    "net_savings": "number"
  },
  "coverage": {
    "average_coverage": "number",
    "on_demand_hours": "number",
    "covered_hours": "number"
  },
  "recommendations": [
    {
      "type": "COMPUTE_SP | EC2_INSTANCE_SP",
      "payment_option": "string",
      "term": "string",
      "hourly_commitment": "number",
      "upfront_cost": "number",
      "estimated_monthly_savings": "number",
      "estimated_savings_percentage": "number",
      "estimated_roi": "number",
      "recommendation_details": {
        "account_scope": "PAYER | LINKED",
        "lookback_period": "string",
        "current_average_hourly_on_demand_spend": "number",
        "current_maximum_hourly_on_demand_spend": "number",
        "estimated_average_utilization": "number",
        "estimated_average_coverage": "number"
      }
    }
  ],
  "analysis_summary": {
    "total_potential_monthly_savings": "number",
    "current_monthly_commitment": "number",
    "recommended_additional_commitment": "number",
    "analysis_period": "string",
    "generated_at": "string"
  }
}
```

## エラーハンドリング

- AWS API エラー時は適切なエラーメッセージを返す
- 権限不足の場合は必要な IAM ポリシーを提示
- データが存在しない場合は空の配列を返す

## 使用例

```
/savings-plans-analyze
/savings-plans-analyze --lookback-period 60
/savings-plans-analyze --payment-option NO_UPFRONT --term THREE_YEARS
```

## 必要な IAM 権限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetSavingsPlansPurchaseRecommendation",
        "ce:GetSavingsPlansUtilization",
        "ce:GetSavingsPlansCoverage",
        "savingsplans:DescribeSavingsPlans"
      ],
      "Resource": "*"
    }
  ]
}
```

## 注意事項

- Savings Plans の推奨事項は過去の使用パターンに基づいて生成される
- 推奨事項は保証ではなく、実際の節約額は使用パターンによって変動する
- Organization の管理アカウントまたは適切な権限を持つアカウントで実行する必要がある
