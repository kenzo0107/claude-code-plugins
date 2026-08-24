# self-review

PR作成前に自分のコミットをセルフレビューし、受けたレビュー指摘を知見として蓄積するプラグイン。
レビューを受けるたびに知見が増え、セルフレビューの精度が育つ。

参考: [レビューをスキルに蓄積する (Mercari Engineering Blog)](https://engineering.mercari.com/blog/entry/20260630-b22667b4d6/)

## 仕組み

```
┌─────────────────┐    照合     ┌──────────────────────────┐
│ /self-review     │ ◄────────── │ skills/self-review/       │
│ PR作成前レビュー   │            │   references/learnings/   │
└─────────────────┘            │   (レビュー知見・Git管理)    │
                                └──────────────────────────┘
┌─────────────────┐    追記            ▲
│ /learn-review    │ ───────────────────┘
│ 受けたレビューを   │   一般化・マスキングして蓄積
│ 知見化           │
└─────────────────┘
```

- **知見の原本はGit** (このリポジトリ)。`/learn-review` はプラグインキャッシュではなく
  ソースリポジトリの `learnings/` に追記する
- 個人名は記録せず、プロダクト名等は先頭数文字を残してマスキングする

## コマンド

### /self-review [base]

現在のブランチのコミット(ベースブランチとの差分)をレビューする。

- 基本観点(正しさ/セキュリティ/テスト/設計/可読性/運用)でのレビュー
- 蓄積した知見(learnings)との照合。ヒットした指摘にはルールIDを付ける
- 指摘は Must / Should / Nits の3段階で報告

```
/self-review                  # ベースブランチ自動判定
/self-review origin/develop   # ベースブランチ指定
```

### /learn-review [PR番号|URL]

PRで受けたレビューコメントを収集し、一般化できる指摘を知見として蓄積する。

- `gh` でレビューコメントを収集(コード行に紐づく指摘を含む)
- 一般化できる指摘だけを選別し、ユーザーの承認を得てから追記
- 追記先は言語別ファイル (`general.md` / `go.md` / `python.md` / `terraform.md` など)

```
/learn-review          # 現在のブランチのPRを対象
/learn-review 123      # PR番号指定
```

## 推奨ワークフロー

1. 実装・コミット
2. `/self-review` — 指摘があれば修正
3. PR作成 (`local-llm:commit-push-pr` 等)
4. レビューを受けて対応・マージ
5. `/learn-review` — 受けた指摘を知見化して蓄積
6. 次回の `/self-review` から新しい知見が照合される

## 知見ファイルのフォーマット

`skills/self-review/references/learnings/README.md` を参照。
