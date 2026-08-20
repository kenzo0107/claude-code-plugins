---
allowed-tools: Bash(./gradlew *), Bash(find *), Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*)
description: Androidプロジェクトをビルドし、失敗時はローカルLLMが原因を診断する(クラウド利用枠を消費しない)
user-invocable: true
---

# android-build: Androidビルド(失敗時はローカルLLMで診断)

カレントディレクトリ(またはその配下)に `gradlew` があるAndroidプロジェクトを対象に、
指定タスクでビルドする。ビルド自体は通常の `./gradlew` 実行(決定的な処理)で行い、
失敗した場合の原因診断だけをローカルLLM(Ollama)に任せる。

## 実行手順

### ステップ1: プロジェクト確認

```bash
find . -maxdepth 2 -name gradlew
```

見つからない場合: Androidプロジェクトのルートで実行するようユーザーに伝えて終了する。

### ステップ2: ビルド実行

タスクは引数で指定可能(未指定なら `assembleDebug`)。例: `/android-build testDebugUnitTest`、
`/android-build lint`。

```bash
./gradlew ${1:-assembleDebug} 2>&1 | tee /tmp/android_build.log
```

### ステップ3: 結果判定

- `BUILD SUCCESSFUL` の場合: 生成された成果物があれば報告する
  ```bash
  find . -path "*/build/outputs/apk/*" -name "*.apk" -newer /tmp/android_build.log -o -path "*/build/outputs/apk/*" -name "*.apk" -mmin -5
  ```
  (直近のビルドで生成されたものに絞る簡易チェック。無ければ省略してよい)
- `BUILD FAILED` の場合: ステップ4へ

### ステップ4: 失敗診断(ローカルLLM)

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: その旨を伝え、通常通り自分でログを読んで
  診断する(ブロッカーにしない)
- 使える場合:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/android_log_review.py /tmp/android_build.log
  ```
  出力された原因・修正案をそのままユーザーに提示する(自分の言葉で書き直さない)。
  ログの内容と明らかに食い違う場合のみ自分で補足する。

## 注意

- 既定モデルは `gemma4:12b`。変更は環境変数 `LOCAL_REVIEW_MODEL`
- 診断は参考情報(偽陽性あり得る)。最終的な修正判断は人間が行う
