# Q/L/D Framework for Monthly Reports

## Overview

The Q/L/D framework categorizes engineering value into three dimensions:

- **Q (Quality)**: Reliability, correctness, safety, risk reduction
- **L (Leverage)**: Efficiency, automation, reusability, scalability
- **D (Delivery)**: Business value, user impact, stakeholder collaboration

Not every month requires entries in all three categories. Choose the categories that best represent the value created that month.

## Decision Tree for Categorization

### Start Here: What was the primary value?

```
Did this work improve RELIABILITY or REDUCE RISK?
  ├─ Yes → Likely Quality (Q)
  │   └─ Examples: Testing, bug fixes, security, refactoring
  │
  ├─ Did this work create REUSABLE VALUE or SAVE FUTURE TIME?
  │   ├─ Yes → Likely Leverage (L)
  │   │   └─ Examples: Automation, tools, documentation
  │   │
  │   └─ No → Was this work DIRECTLY REQUESTED by users/stakeholders?
  │       ├─ Yes → Likely Delivery (D)
  │       │   └─ Examples: Features, bug fixes, integrations
  │       │
  │       └─ No → Reconsider the value created
```

## Quality (Q) - Deep Dive

### When to Use Quality

Use Q when the work:
- Prevents future problems
- Improves system reliability
- Reduces technical debt
- Enhances code quality
- Mitigates security risks
- Improves test coverage
- Refactors for maintainability

### Quality Patterns

#### Pattern 1: Risk Mitigation

**Template:** `[調査・設計] により [リスク] を [回避・低減]`

**Examples:**
- "削除対象の影響範囲（DB連携・外部API呼び出し）を事前に調査した上で、安全に除去できる順序を設計し、19 PRに分割して段階的に実施。技術的負債の解消と後続開発のリスク低減を実現"
- "DB Aurora MySQL移行で無事故完了。DMS レプリケーション整備からメンテナンス実施まで一貫して担当"

#### Pattern 2: Quality Improvement

**Template:** `[改善施策] により [品質指標] を [改善]`

**Examples:**
- "月間50+ PR作成・マージ、10リポジトリ横断でレビュー20+件実施。コードレビューを通じて品質向上に貢献"
- "mobile-app AndroidのCompose化で計17+画面を移行完了。content-app KMP移行ではデータ層からUI層まで3リポジトリ横断で品質を担保"

#### Pattern 3: Process Excellence

**Template:** `[プロセス] を [工夫] し、[品質成果]`

**Examples:**
- "担当者と密にコミュニケーションをとりながら、仕様・QAフィードバックを迅速に取り込み、各機能を最適な形で本番リリースまで完遂"

### Quality Anti-Patterns

❌ **Avoid:**
- "バグを修正した" (too vague - what bug? what impact?)
- "コードレビューした" (activity, not value - how many? what improvements?)
- "テストを書いた" (how many? what coverage increase?)

✅ **Instead:**
- "認証フローのセキュリティ脆弱性（影響ユーザー10万人）を特定・修正し、本番リリース前に対処"
- "20件のコードレビューを通じて、型安全性の問題5件、パフォーマンス問題3件を事前に発見・修正"
- "カバレッジを60%→85%に向上、クリティカルパス100%をカバー"

## Leverage (L) - Deep Dive

### When to Use Leverage

Use L when the work:
- Automates repetitive tasks
- Creates reusable tools/libraries
- Enables others to work faster
- Scales to multiple use cases
- Systematizes knowledge
- Reduces future manual work

### Leverage Patterns

#### Pattern 1: Automation Impact

**Template:** `[自動化] により [工数削減・効率化] を実現`

**Examples:**
- "GitHub Actions Node.js 20非推奨対応を8リポジトリで一括対応し、CI障害リスクを未然防止。Ruby 3.2更新と未使用Gemfile削除でビルド環境を統一"
- "Claude Codeのスラッシュコマンド（日報・月報自動生成、Compose移行コマンド）を継続的に活用しレポーティング・実装工数を削減"

#### Pattern 2: Tool/Infrastructure Creation

**Template:** `[ツール・基盤] を構築し、[再利用性・拡張性] を実現`

**Examples:**
- "auto-approveワークフローのGroovy DSL対応によりバージョンアップPRの自動承認を安定化"
- "Devinのワンショット開発ワークフローを整備し、非エンジニアでも開発に参加できる環境を推進"

#### Pattern 3: Cross-Repository Impact

**Template:** `[施策] を [N]リポジトリで展開し、[組織的効果]`

**Examples:**
- "GitHub Actions Node.js 20非推奨対応を8リポジトリで一括対応"
- "10リポジトリ横断でレビュー20+件実施"

### Leverage Anti-Patterns

❌ **Avoid:**
- "ツールを使った" (using ≠ creating leverage)
- "効率化した" (how? how much? who benefits?)
- "自動化した" (what was automated? time saved?)

✅ **Instead:**
- "PR作成を自動化するスクリプトを作成し、チーム全体で週10時間の工数削減"
- "8リポジトリで一括対応可能な依存関係更新ツールを構築"
- "日報生成を自動化し、毎日15分の記録作業を削減"

## Delivery (D) - Deep Dive

### When to Use Delivery

Use D when the work:
- Directly addresses user needs
- Delivers requested features
- Solves customer problems
- Coordinates with stakeholders
- Makes technical decisions impacting product
- Responds to business requirements

### Delivery Patterns

#### Pattern 1: Problem Solving

**Template:** `[課題] に対して [調査・実装] を行い、[解決]`

**Examples:**
- "データ取込不具合についてCS問い合わせからソースコード調査を実施し、根本原因を特定"
- "「本日の営業時間」表示ロジック改善により、ユーザー混乱を解消"

#### Pattern 2: Stakeholder Collaboration

**Template:** `[ステークホルダー] と [調整・協議] し、[成果]`

**Examples:**
- "顧客要望を技術的に整理し、PdMと仕様を確定"
- "API仕様v2.5/2.6のSTG反映を主導し、関連チームに動作確認用QRコードを共有"

#### Pattern 3: Feature Delivery

**Template:** `[機能] を [実装・リリース] し、[ユーザー価値]`

**Examples:**
- "AI転職エージェントPoCで医師と求人のマッチングAI精度が良好との評価を獲得"
- "キーメッセージ一括複製機能を本番リリース完了し、運用効率を向上"

### Delivery Anti-Patterns

❌ **Avoid:**
- "機能を追加した" (what feature? who requested? why valuable?)
- "ユーザーの要望に対応" (what request? how did you solve it?)
- "プロジェクトを完了" (what was delivered? what value?)

✅ **Instead:**
- "PdMからの要望を受け、検索速度を3秒→0.5秒に改善し、ユーザー離脱率20%削減"
- "CSからのエスカレーション3件を調査・修正し、顧客満足度向上に貢献"
- "新機能リリースにより、月間アクティブユーザーが15%増加"

## Complex Cases: Multiple Categories

Some work spans multiple categories. Choose the **primary value** or split into multiple bullets:

### Example 1: Security Fix with Automation

**Primary value: Q (prevents risk)**
```
**Q:** 認証フローのセキュリティ脆弱性を特定・修正（影響ユーザー10万人）。
併せて、同様の脆弱性を自動検知するlintルールを追加し、再発防止を実現。
```

Or split:
```
**Q:** 認証フローのセキュリティ脆弱性を特定・修正（影響ユーザー10万人）
**L:** 同様の脆弱性を自動検知するlintルールを追加し、再発防止を実現
```

### Example 2: Feature with Infrastructure

**Primary value: D (user-facing feature)**
```
**D:** 新検索機能をリリースし、検索速度を3秒→0.5秒に改善。
インフラ最適化により、将来的な機能追加も容易に。
```

Or split:
```
**D:** 新検索機能をリリースし、検索速度を3秒→0.5秒に改善
**L:** 検索基盤を再設計し、将来的な機能追加を容易化
```

## Monthly Report Q/L/D Balance

### Typical Patterns by Role/Phase

**Infrastructure/SRE Focus:**
- Q: 60-80% (reliability, operations)
- L: 20-40% (automation, tools)
- D: 0-20% (stakeholder requests)

**Feature Development Focus:**
- Q: 20-40% (code quality, testing)
- L: 10-30% (reusable components)
- D: 40-70% (user-facing features)

**Technical Leadership:**
- Q: 30-50% (architecture decisions)
- L: 20-40% (team enablement)
- D: 30-40% (stakeholder alignment)

**Not all months need balance** - focus on what created the most value that month.

## Decision Examples

### Example 1: Database Migration

**Question:** Is DB migration Q, L, or D?

**Analysis:**
- Primary value: Reliability improvement (modern DB, better support)
- Secondary value: Future scalability
- **Category: Q** (with L mention if infrastructure enables future work)

**Write as:**
```
**Q:** DB Aurora MySQL移行を完遂（無事故）。DMS レプリケーション整備から
メンテナンス実施まで一貫して担当。Aurora移行により、将来的な拡張性も向上。
```

### Example 2: Automated PR Creation Tool

**Question:** Is automation tool Q, L, or D?

**Analysis:**
- Primary value: Saves future time for team
- Secondary value: Reduces manual errors (Q)
- **Category: L** (creates leverage for team)

**Write as:**
```
**L:** PR作成自動化ツールを構築し、チーム全体で週10時間の工数削減を実現。
手動作成時のミスも削減。
```

### Example 3: Customer-Reported Bug Fix

**Question:** Bug fix is Q or D?

**Analysis:**
- Depends on **who reported** and **impact**:
  - **Internal discovery** → Q (proactive quality improvement)
  - **Customer reported** → D (responding to user need)
  - **High-impact/security** → Q (risk mitigation)

**Write as D (customer-reported):**
```
**D:** CSエスカレーションの決済バグを調査・修正。根本原因を特定し、
影響ユーザー200名に対して個別フォローを実施。
```

**Write as Q (proactive discovery):**
```
**Q:** 決済フローの潜在的バグを発見・修正。本番影響前に対処し、
データ不整合を防止。
```

## Quick Reference Table

| Work Type | Q | L | D | Notes |
|-----------|---|---|---|-------|
| Bug fix (proactive) | ✅ | | | Risk reduction |
| Bug fix (user-reported) | | | ✅ | User value |
| Security patch | ✅ | | | Risk mitigation |
| Automation tool | | ✅ | | Future efficiency |
| Feature delivery | | | ✅ | User-facing |
| Refactoring | ✅ | | | Code quality |
| Infrastructure | ✅ | ✅ | | Depends on focus |
| Documentation | | ✅ | | Knowledge sharing |
| Performance tuning | ✅ | | ✅ | Depends on driver |
| Code review | ✅ | | | Quality gate |
| Tech debt cleanup | ✅ | | | Risk reduction |
| CI/CD improvement | | ✅ | | Team efficiency |

## Summary

**Choose Q when:** Work prevents problems, improves reliability, reduces risk
**Choose L when:** Work saves future time, enables others, creates reusable value
**Choose D when:** Work delivers user value, solves customer problems, addresses stakeholder needs

**Default guideline:** If work was requested by users/stakeholders → D. If work enables future efficiency → L. If work improves safety/quality → Q.

When in doubt, choose the category that best represents **why this work mattered** to the organization.
