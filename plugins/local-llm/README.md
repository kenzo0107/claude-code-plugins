# local-llm

ローカルLLM(Ollama)でクラウドLLMの利用枠を消費せずに定型作業を行うプラグイン。

## 前提

- [Ollama](https://ollama.com/) 0.32以降: `brew install ollama && brew services start ollama`
- モデル: `ollama pull gemma4:12b`(約8GB。メモリ16GB以上のMac推奨)
- コミットメッセージ生成には `ollama pull qwen3.6:27b`(約17GB)も必要
  (精度検証の結果、複数変更を含むdiffの箇条書き分解はgemma4:12bでは不正確だったため)
- `/android-*` コマンドを使う場合はAndroid SDK(`adb` `emulator` がPATH、または
  `ANDROID_HOME`/`ANDROID_SDK_ROOT` から解決できること)

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
既定モデルは `qwen3.6:27b`(約30〜40秒)。実際のdiff(機能追加・バグ修正・リネームの3種の
変更を混在させたテスト)で比較したところ、`gemma4:12b` は複数変更を1行に圧縮し規約の
箇条書き分解ができなかったのに対し、`qwen3.6:27b` はClaudeが書く案と同等の精度だった。

### /pr-body [base]

ブランチ差分からGitHub PRの本文(Summary/Test plan)をローカルLLMで生成する。

```
/pr-body                # デフォルトブランチとの差分
/pr-body origin/main    # 指定refとの差分
```

### /code-review [base]

Go/Python/Ruby/Kotlin/TypeScriptのコード差分をセキュリティ・品質観点でローカルLLMがプレレビューする。
差分に含まれる拡張子から観点ファイルを自動選択する(`scripts/code_review.py --auto`)。
同梱観点: `rules/go-security.md` `python-security.md` `ruby-security.md` `kotlin-android.md`
`typescript-security.md`(言語別セキュリティ)、`general-quality.md`(言語非依存の品質。`/pr-review` で使用)。
精度は local-llm リポジトリの `evals/` で継続測定している(`evals/RESULTS.md`)。

### /pr-review <PR番号|URL> [--repo owner/repo]

他人のPRを `gh pr diff` で取得し、言語別セキュリティ観点+一般品質観点でローカルLLMがプレレビューして
レビューコメント案(要確認/参考)を Markdown で出す。投稿はユーザーが内容を確認してから
`gh pr review --comment` で行う(勝手に投稿しない)。

### /summarize <file|-> [--mode log|ci|diff|text] [--lines N] [--question "..."]

長いログ・CI出力・diff・文書を要約する。入力の種類は自動判定、長い入力は分割→統合。
「読んで要点を抜き出す」だけの作業をクラウドから逃がす用途。

### /anonymize <file|->

ログ・テキストの個人情報をマスクする。メール・IP・電話番号は正規表現で機械的に置換し、人名など
文脈依存のものはローカルLLMに列挙させてコード側で置換。最後に正規表現で再走査し、漏れ疑いがあれば exit 2。
クラウドLLMにログを渡す前の前処理。変換表 `*.map.json` は個人情報そのものなので外に出さない。

### /android-build [task]

Androidプロジェクト(`gradlew` があるディレクトリ)をビルドする。ビルド自体は通常の
`./gradlew` 実行で行い、失敗した場合の原因診断だけをローカルLLMに任せる。

```
/android-build                    # ./gradlew assembleDebug
/android-build testDebugUnitTest  # 任意のGradleタスクを指定
```

### /android-install

実機/エミュレータの起動確認(無ければAVDを起動)→ `./gradlew installDebug` でビルド・
インストールまでを一括で行う。失敗時(ビルド失敗・`INSTALL_FAILED_*` など)の原因診断を
ローカルLLMに任せる。

### /android-release [APK|AAB]

リリースAPK(`assembleRelease`、既定)またはAAB(`bundleRelease`)を生成する。署名設定が
無い場合は未署名になる旨を先に警告する。失敗時の原因診断をローカルLLMに任せる。

### /commit-push-pr

ブランチ作成・コミット・push・PR作成を一括で行う。公式 `commit-commands:commit-push-pr`
と同等の作業を、メッセージ・本文の生成にローカルLLMを使って行う版。

> **公式 `commit-commands:commit` / `commit-commands:commit-push-pr` との違い**:
> 公式コマンドは `allowed-tools` が git/gh 系のみに絞られており、プロンプトも
> 「他のツールは使うな」と明記しているため、本プラグインの自動発火スキル
> (`python3` が必要)はその実行中には発火できない。同等の作業をローカルLLMで
> 行いたい場合は、公式コマンドではなく `/commit-msg`(= `/commit` 相当)や
> `/commit-push-pr`(= `/commit-push-pr` 相当)をこちらのプラグインから使うこと。

### /clean-merged-branches

`main` / `master` / `develop` を除くローカルブランチのうち、マージ済みで
`git branch -d`(safe delete)が成功するものだけをまとめて削除する。`-D`(force)は使わない
ため、未マージの作業ブランチを誤って消すことはない。ローカルLLMは使わない純粋なgit操作だが、
他のコマンドと合わせて日常的に使うため本プラグインに同梱している。

### /git-status-color

`git status` の内容を、ステージ済み(緑)/未ステージ・未追跡(赤)に色分けして表示する。
1ファイルが両方の状態を持つ場合(`git add` 後にさらに編集した場合など)は両方に表示される。
`git status --porcelain` の解析のみの決定的処理で、ローカルLLMは使わない。

## git push 前の自動プレレビュー(フック)

`hooks/hooks.json` の PreToolUse フックが、Claude Code が `git push` を実行する直前に push 対象の差分
(`@{upstream}` または `origin/<default>` との差分)をローカルLLMでプレレビューする。
`.tf` は MedPeer 規約、`.go/.py/.rb/.kt/.ts` 等は言語別セキュリティ観点。

- high confidence の指摘あり → 権限確認(ask)として指摘を表示し、ユーザーが push を続けるか判断する
- low のみ / 指摘なし → そのまま push(指摘は Claude に渡され、報告に含まれる)
- Ollama 未起動・対象差分なし・差分が巨大(120k文字超)→ 何もしない
- 同じ HEAD への再 push はキャッシュを返す(承認後に待たせない)
- 無効化: 環境変数 `LOCAL_LLM_SKIP_PUSH_REVIEW=1`
- フックの変更は Claude Code の再起動後に反映される

## 自動発火するスキル

`/tf-review` `/commit-msg` `/pr-body` `/code-review` `/pr-review` `/summarize` `/anonymize` は、対応する場面
(Terraform差分のレビュー・コミット作成・PR作成・対応言語の差分レビュー・他人のPRレビュー・長い出力の要約・
個人情報を含むログの分析前)で
Claude Codeが自律的に判断してスキルとしても呼び出す(`user-invocable: false`)。
Ollamaが起動していない場合はスキップされ、通常のクラウドLLMでの処理にフォールバックする
(ブロッカーにはしない)。

- モデル変更: いずれも環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b、commit-msgのみ
  qwen3.6:27b。tf-reviewのみ `TF_REVIEW_MODEL`)

`/android-build` `/android-install` `/android-release` はエミュレータ起動・実機への
インストール・リリース生成という副作用の大きい操作を含むため、自動発火はさせずコマンド
実行のみとしている(失敗時の原因診断部分だけがローカルLLMを使う)。

`/clean-merged-branches` はブランチ削除という取り消しにくい操作を含むため、同様に
自動発火はさせずコマンド実行のみとしている。

`/git-status-color` はローカルLLMを使わない純粋な表示コマンドのため、そもそも自動発火スキル
としては提供していない(ユーザーが見たいときにコマンドで呼ぶ用途)。

## 共通設定(環境変数)

| 変数 | 既定 | 用途 |
|---|---|---|
| `LOCAL_REVIEW_MODEL` | gemma4:12b(commit-msg は qwen3.6:27b) | 各スクリプトのモデル |
| `TF_REVIEW_MODEL` / `TF_REVIEW_RULES` | gemma4:12b / medpeer-terraform の SKILL.md | tf-review のモデル・規約ファイル |
| `LOCAL_LLM_MAX_NUM_CTX` | 32768 | 入力に応じて自動拡張する num_ctx の上限 |
| `LOCAL_LLM_MAX_CHUNK_CHARS` | 24000 | これを超える差分はファイル単位に分割して処理 |
| `LOCAL_LLM_THINK` | 0 | 1 で thinking を有効化(遅くなる。精度比較用) |
| `LOCAL_LLM_QUIET` | 0 | 1 で stderr の進捗表示を抑止 |
| `LOCAL_LLM_SKIP_PUSH_REVIEW` | 0 | 1 で push 前フックを無効化 |

指定モデルが無い場合は `gemma4:12b` に自動フォールバックする(stderr に表示)。

## 開発

`scripts/` `rules/` `hooks/*.py` の編集元は [kenzo0107/local-llm](https://github.com/kenzo0107/local-llm) の `tools/` で、
そこから `scripts/sync-plugin.sh` でコピーして同期する(このディレクトリを直接編集しない)。
精度の回帰テストも local-llm リポジトリの `evals/` で行う。

## 設計方針

制御フローはスクリプトで固定し、判断が必要な箇所だけローカルLLMを呼ぶ。全スクリプトは共通クライアント
(`scripts/ollama_client.py`)を通り、system/user メッセージの分離と指示の再掲、JSON Schema による出力強制、
入力量に応じた num_ctx 拡張、大きな差分のファイル単位分割を一律に適用する。
LLMの出力は機械検証(マスク漏れ再走査など)や人間の最終確認で品質を担保する。
生成系(コミットメッセージ・PR本文)は「ローカルLLMの出力をそのまま使う」ことが目的なので、
Claudeが結果を自分の言葉で書き直すことはしない。
