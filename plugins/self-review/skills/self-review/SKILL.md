---
name: self-review
description: PR作成前に自分のコミット(ブランチ差分)をエンジニア視点でセルフレビューする。「セルフレビュー」「PR作成前にレビュー」「自分のコミットをレビュー」と依頼された時、またはPR作成(commit-push-pr等)の直前に使用する。蓄積されたレビュー知見(learnings)を照合し、過去に受けた指摘の再発を防ぐ。
user-invocable: false
---

# self-review スキル: PR作成前のセルフレビュー

自分のコミットをPR作成前にレビューし、レビュアーに指摘される前に問題を潰す。
過去に受けたレビュー指摘から蓄積した知見(learnings)を毎回照合するのが最大の特徴で、
`/learn-review` で知見が増えるほどレビュー精度が上がる。

## 実行手順

### 1. レビュー対象の特定

```bash
git branch --show-current
git remote show origin | grep 'HEAD branch'   # ベースブランチの特定
```

- ベースブランチ上にいる場合は「レビュー対象のブランチ差分がない」と伝えて終了する
- 未コミットの変更がある場合は、レビュー対象に含めるかユーザーに確認する

```bash
BASE=$(git merge-base origin/<base> HEAD)
git log --oneline $BASE..HEAD
git diff $BASE...HEAD
```

### 2. レビュー観点と蓄積知見の読み込み

1. `references/review-perspectives.md` を読み、基本レビュー観点を把握する
2. `references/learnings/` 配下を読み込む:
   - `general.md` は必ず読む
   - 差分に含まれるファイル種別に対応するものを追加で読む
     (例: `.go` → `go.md`、`.py` → `python.md`、`.tf` → `terraform.md`、`.rb` → `ruby.md`。
     存在しないファイルはスキップ)

知見の最新版がプラグインキャッシュより新しい可能性があるため、ソースリポジトリが
ローカルにあればそちらを優先する:

```bash
ghq list -p kenzo0107/claude-code-plugins 2>/dev/null
```

見つかればそのリポジトリ内の `plugins/self-review/skills/self-review/references/` を、
見つからなければ `${CLAUDE_PLUGIN_ROOT}/skills/self-review/references/` を読む。

### 3. レビュー実施

差分全体に対して以下を行う:

1. **基本観点レビュー**: `review-perspectives.md` の各観点で差分を確認する
2. **知見照合**: 読み込んだ learnings の各ルールについて、差分に該当箇所がないか
   1件ずつ確認する。該当した場合は指摘にルールID(例: `GO-003`)を明記する
3. **コミット単位の確認**: コミットメッセージが変更内容を具体的に表しているか、
   コミットの粒度が適切か(無関係な変更の混在がないか)を確認する

推測で指摘しない。指摘は差分内の具体的な行を根拠にする。差分だけで判断できない場合は
周辺コードをReadして裏を取ってから指摘する。

### 4. 結果の報告

以下の3段階で報告する。該当なしの区分は省略する。

- **Must (修正すべき)**: バグ・セキュリティ問題・データ破壊の可能性など
- **Should (修正を推奨)**: 設計・テスト不足・エラーハンドリング・可読性の問題
- **Nits (好みの範囲)**: 命名・コメント・スタイル

各指摘には `ファイルパス:行番号`、根拠、修正案を付ける。知見照合でヒットした指摘には
ルールIDを付ける(例: `[GO-003] エラーを握りつぶしている`)。

指摘ゼロの場合も「セルフレビュー完了: 指摘なし(照合した知見 N 件)」と報告する。

### 5. 修正の扱い

- 指摘の報告までがこのスキルの役割。修正はユーザーが明示的に依頼した場合のみ行う
- Must がある状態でPR作成に進む場合は、その旨を一言添える

## 他スキルとの関係

- Go/Python/Terraformの差分がある場合、`local-llm:code-review` / `local-llm:tf-review` の
  プレレビューと併用できる(ローカルLLMは機械的な検出、本スキルは知見照合と文脈判断を担当)
- レビューを受けてPRがマージされたら `/learn-review` で指摘を知見として蓄積する

## Additional Resources

### Reference Files

- **`references/review-perspectives.md`** - 基本レビュー観点(正しさ/セキュリティ/テスト/設計/可読性)
- **`references/learnings/README.md`** - 知見ファイルのフォーマット定義
- **`references/learnings/*.md`** - 蓄積されたレビュー知見(general + 言語別)
