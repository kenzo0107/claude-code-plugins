---
allowed-tools: Bash(./gradlew *), Bash(find *), Bash(grep *), Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*)
description: AndroidのリリースAPK/AABを生成する。失敗時はローカルLLMが原因を診断する(クラウド利用枠を消費しない)
user-invocable: true
---

# android-release: リリースAPK/AAB生成(失敗時はローカルLLMで診断)

生成自体は通常の `./gradlew` 実行(決定的な処理)で行い、失敗した場合の原因診断だけを
ローカルLLM(Ollama)に任せる。

## 実行手順

### ステップ1: プロジェクト確認

```bash
find . -maxdepth 2 -name gradlew
```

見つからない場合: Androidプロジェクトのルートで実行するようユーザーに伝えて終了する。

### ステップ2: 形式の確認

引数、または無ければユーザーに確認する:

- APK(`assembleRelease`、既定): 直接インストール・配布用
- AAB(`bundleRelease`): Google Play提出用

### ステップ3: 署名設定の確認

```bash
grep -rn "signingConfigs" --include="build.gradle*" app 2>/dev/null
```

見つからない場合: 生成物が未署名(`*-release-unsigned.apk` 等)になり、そのままでは
実機インストールもPlayへの提出もできない旨を先に伝える(処理は続けてよい。署名設定は
このコマンドの範囲外なのでブロッカーにしない)。

### ステップ4: 生成実行

```bash
./gradlew ${TASK:-assembleRelease} 2>&1 | tee /tmp/android_release.log
```

(`TASK=bundleRelease` を指定した場合はAABを生成)

### ステップ5: 結果判定

- `BUILD SUCCESSFUL` の場合: 生成物を特定して報告する
  ```bash
  find . -path "*/build/outputs/apk/release/*" -name "*.apk"
  find . -path "*/build/outputs/bundle/release/*" -name "*.aab"
  ```
  ファイルサイズ・パス・(ファイル名から判別できれば)署名済みかどうかを伝える。
  未署名の場合は配布前に署名が必要であることを改めて注意する
- `BUILD FAILED` の場合: ステップ6へ

### ステップ6: 失敗診断(ローカルLLM)

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: その旨を伝え、通常通り自分でログを読んで
  診断する(ブロッカーにしない)
- 使える場合:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/android_log_review.py /tmp/android_release.log
  ```
  出力された原因・修正案をそのままユーザーに提示する(自分の言葉で書き直さない)。

## 注意

- 既定モデルは `gemma4:12b`。変更は環境変数 `LOCAL_REVIEW_MODEL`
- 署名鍵(keystore)の作成・管理はこのコマンドでは行わない。既存の設定を前提とする
- 診断は参考情報(偽陽性あり得る)。最終的な修正判断は人間が行う
