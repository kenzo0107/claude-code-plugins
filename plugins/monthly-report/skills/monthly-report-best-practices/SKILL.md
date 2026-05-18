---
name: Monthly Report Best Practices
description: This skill should be used when the user asks to "write a monthly report", "月報の書き方", "Q/L/Dとは", "評価者に伝わる書き方", "具体的な月報", "進化・非停滞の証明", or needs guidance on creating effective engineering monthly reports that clearly communicate achievements to evaluators.
version: 0.1.0
---

# Monthly Report Best Practices

## Purpose

Provide guidance for creating effective engineering monthly reports that clearly communicate achievements, growth, and value to evaluators. Focus on the Q/L/D (Quality/Leverage/Delivery) framework and concrete writing techniques that transform generic activity logs into compelling evidence of professional impact.

## When to Use This Skill

Use this skill when:
- Writing or reviewing monthly engineering reports
- Clarifying Q/L/D categorization
- Improving report specificity and impact
- Demonstrating professional growth
- Structuring evidence and achievements

## Core Report Structure

Monthly reports follow this proven structure:

### ① Main Scope (今月のメインスコープ)

State the month's primary tasks and projects with concrete outcomes:

**Include:**
- Ticket/Epic IDs (MP-1230, JIRA-456, etc.)
- Completion status (本番リリース完了, 実装完了, etc.)
- Project names and phases
- Links to internal documentation

**Example:**
```
- rack3アップグレード（MP-1230）：本番リリース完了
- DB Aurora MySQL移行：メンテナンス実施、無事故完了
- キーメッセージ一括複製機能（MP-1872）：本番リリース完了
```

### ② Value Proof (Valueの証明)

Demonstrate value using Q/L/D framework. Choose categories that best represent the month's work—not all three are required every month.

#### Quality (Q)

Focus on: Reliability, correctness, safety, risk reduction, technical excellence

**Structure:** `[Action] により [具体的な結果・影響]`

**Strong examples:**
- "担当者と密にコミュニケーションをとりながら、仕様・QAフィードバックを迅速に取り込み、各機能を最適な形で本番リリースまで完遂した"
- "削除対象の影響範囲（DB連携・外部API呼び出し・関連サービス）を事前に調査した上で、安全に除去できる順序を設計し、19 PR（main-app 13件・framework 4件...）に分割して段階的に実施"
- "月間50+ PR作成・マージ、10リポジトリ横断でレビュー20+件実施"

**Include:**
- Quantitative metrics (PR count, repositories, test coverage, bug reduction)
- Risk mitigation measures
- Quality improvement processes
- Scope of impact (affected users, services, teams)

#### Leverage (L)

Focus on: Efficiency, automation, reusability, scalability, knowledge sharing

**Structure:** `[工夫・改善] により [時間削減・効率化・再利用性向上]`

**Strong examples:**
- "GitHub Actions Node.js 20非推奨対応を8リポジトリで一括対応し、CI障害リスクを未然防止"
- "Claude Codeのスラッシュコマンド（日報・月報自動生成、Compose移行コマンド）を継続的に活用しレポーティング・実装工数を削減"
- "Ruby 3.2更新と未使用Gemfile削除でビルド環境を統一。auto-approveワークフローのGroovy DSL対応によりバージョンアップPRの自動承認を安定化"

**Include:**
- Tools/processes created
- Cross-repository improvements
- Automation impact
- Knowledge systematization
- Future efficiency gains

#### Delivery (D)

Focus on: Business value, user impact, stakeholder collaboration, problem-solving

**Structure:** `[課題・要求] に対して [技術判断・調整・実装] を行い [結果・価値]`

**Strong examples:**
- "データ取込不具合についてCS問い合わせからソースコード調査を実施し、根本原因を特定"
- "顧客要望を技術的に整理し、PdMと仕様を確定"
- "API仕様v2.5/2.6のSTG反映を主導し、関連チームに動作確認用QRコードを共有"

**Include:**
- Business problems solved
- Stakeholder coordination
- User-facing improvements
- Technical decisions impacting product

**For detailed Q/L/D categorization guidance, see `references/qld-framework.md`**

### ③ Growth & Non-Stagnation Proof (進化・非停滞の証明)

Demonstrate professional evolution—new skills, expanded scope, improved capabilities:

**Strong patterns:**
- **New technology adoption**: "KMP（Kotlin Multiplatform）でのクロスプラットフォーム開発：全レイヤーを一人で実装"
- **Expanded domain**: "インフラ/DevOps領域への対応拡大：リポジトリ横断の改善をリード"
- **Process improvement**: "削除・整理作業に「安全性の設計」を持ち込む意識"
- **Capability increase**: "複数リポジトリを横断した自走力：各リポジトリの構造・CIルールへの適応コストが下がってきている"

**Include:**
- Skills learned this month
- Domain expansion
- Improved approaches to familiar tasks
- Faster/more reliable execution

**Avoid:**
- Generic statements ("learned a lot", "improved skills")
- Listing tools used without demonstrating mastery
- Repeating previous months' growth claims

### ④ Evidence (エビデンス)

Provide verifiable links to work performed:

**Organize by category:**
```
### DB Migration (70%)
  - DMS レプリケーション整備
    - [PR #2112](URL)
    - [PR #2113](URL)
  - DB ユーザー設定
    - [PR #2109](URL)

### CI/CD対応 (20%)
  - [PR #2017: Node.js 20対応](URL)
  - [PR #952: Actions更新](URL)
```

**Best practices:**
- Group PRs by project/theme
- Indicate task weight (percentage or priority)
- Include brief context for each PR
- Link to design documents for major projects

## Writing for Impact

### Use Specific Numbers

**Weak:** "多くのPRを作成した"
**Strong:** "月間50+ PR作成・マージ、10リポジトリ横断でレビュー20+件実施"

**Weak:** "パフォーマンスを改善"
**Strong:** "API応答速度を30%改善（平均200ms→140ms）"

### Explain the "Why" and "How"

**Weak:** "機能を実装した"
**Strong:** "顧客要望を技術的に整理し、PdMと仕様を確定した上で実装"

**Weak:** "リファクタリングした"
**Strong:** "削除対象の影響範囲を事前に調査した上で、安全に除去できる順序を設計し、19 PRに分割して段階的に実施"

### Avoid Vague Terms

Replace generic verbs with specific actions:

- ❌ "改善した" → ✅ "API応答速度を30%改善"
- ❌ "調整した" → ✅ "認証フローを再設計し、セキュリティ要件を満たすよう変更"
- ❌ "対応した" → ✅ "CS問い合わせから根本原因を特定し、修正PRをマージ"

### Show Impact Scope

Always indicate who/what was affected:

- "8リポジトリで一括対応"
- "関連チームに動作確認用QRコードを共有"
- "全ユーザーに影響する機能"
- "月間1000件の処理を自動化"

## Weekly Recording Strategy

Since reports are built incrementally, record weekly:

**Capture immediately:**
- PR URLs and brief description
- Ticket numbers
- Key decisions and their context
- Unexpected challenges and solutions
- Learning moments

**Weekly reflection prompts:**
- What was the main achievement this week?
- What did I learn or improve?
- What problems did I solve?
- How did this create value?

Accumulate these notes in `.claude/monthly-report-draft.md` for easy monthly synthesis.

## Common Pitfalls

### Pitfall 1: Activity Log Instead of Impact

**Wrong approach:**
```
- PR #123をマージ
- PR #456をレビュー
- ミーティングに参加
```

**Correct approach:**
```
### Q: 基盤移行後の旧処理を体系的に整理・削除
削除対象の影響範囲を事前に調査した上で、19 PRに分割して段階的に実施。
技術的負債の解消と後続開発のリスク低減を実現。
```

### Pitfall 2: Omitting Context

**Wrong:** "機能を追加"
**Correct:** "セグメント会議でのフィードバックを受け、求人提案精度を改善するUI変更を実装"

### Pitfall 3: No Quantification

**Wrong:** "多くのリポジトリで対応"
**Correct:** "8リポジトリで一括対応し、CI障害リスクを未然防止"

### Pitfall 4: Copy-Pasting PR Titles

Transform PR titles into achievement statements:

**PR title:** "Update dependencies"
**Report entry:** "ライブラリ脆弱性対応として8リポジトリ横断で依存関係を更新、セキュリティリスクを解消"

## Additional Resources

### Reference Files

For comprehensive guidance on specific topics:

- **`references/best-practices.md`** - Detailed analysis of excellent monthly reports with annotated examples
- **`references/qld-framework.md`** - Complete Q/L/D framework with categorization decision trees

### Example Files

Study working examples in `examples/`:

- **`examples/good-report-example.md`** - Exemplary monthly report with annotations
- **`examples/bad-report-example.md`** - Common mistakes with corrections

## Quick Checklist

Before submitting a monthly report:

- [ ] Main scope includes ticket IDs and completion status
- [ ] Q/L/D sections have concrete numbers
- [ ] Each achievement explains "why" and "how"
- [ ] No vague terms ("改善", "調整" without details)
- [ ] Impact scope indicated (repositories, users, teams)
- [ ] Growth section shows new capabilities, not just tool usage
- [ ] Evidence organized by theme with context
- [ ] All PRs and documents linked

Use this checklist when reviewing reports to ensure maximum evaluator comprehension and impact.
