---
allowed-tools: Bash(adb *), Bash(emulator *), Bash(./gradlew *), Bash(find *), Bash(command -v *), Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*)
description: エミュレータを起動し、Androidアプリをビルド・インストールする。失敗時はローカルLLMが原因を診断する(クラウド利用枠を消費しない)
user-invocable: true
---

# android-install: エミュレータ起動 + ビルド・インストール(失敗時はローカルLLMで診断)

実機/エミュレータの起動確認・ビルド・インストールは通常のシェル実行(決定的な処理)で行い、
失敗した場合の原因診断だけをローカルLLM(Ollama)に任せる。

## 実行手順

### ステップ1: プロジェクト確認

```bash
find . -maxdepth 2 -name gradlew
```

見つからない場合: Androidプロジェクトのルートで実行するようユーザーに伝えて終了する。

### ステップ2: SDKツールの確認

```bash
command -v adb
command -v emulator
```

見つからない場合は `${ANDROID_HOME:-$ANDROID_SDK_ROOT}/platform-tools/adb` /
`${ANDROID_HOME:-$ANDROID_SDK_ROOT}/emulator/emulator` を試す。どちらのパスも無ければ
Android SDKの導入場所をユーザーに確認して終了する。以降 `adb` `emulator` は解決したパスを使う。

### ステップ3: 実機/エミュレータの起動確認

```bash
adb devices
```

- `device` 状態(`offline`/`unauthorized` は除く)の端末が既にあれば起動をスキップしステップ5へ
- 無ければステップ4でエミュレータを起動する

### ステップ4: エミュレータ起動

```bash
emulator -list-avds
```

- AVDが1つならそれを使う。複数あればユーザーに選んでもらう。0件ならAndroid Studioの
  Device ManagerでのAVD作成を案内して終了する

```bash
nohup emulator -avd <AVD名> -netdelay none -netspeed full > /tmp/android_emulator.log 2>&1 &
adb wait-for-device
```

起動完了(ホームスクリーンが使える状態)まで待つ。最大2分程度、5秒間隔でポーリングする:

```bash
timeout 120 bash -c 'until adb shell getprop sys.boot_completed 2>/dev/null | grep -q 1; do sleep 5; done'
```

タイムアウトした場合は `/tmp/android_emulator.log` を確認し、ユーザーに状況を報告する
(起動待ちで止め続けない)。

### ステップ5: ビルド + インストール

```bash
./gradlew installDebug 2>&1 | tee /tmp/android_install.log
```

(`installDebug` はビルドと `adb install` を1タスクで行う)

### ステップ6: 結果判定

- 成功: アプリのパッケージ名を特定し、起動コマンドを案内する(起動の実行はユーザー判断)
  ```bash
  find . -name "AndroidManifest.xml" -path "*/main/*"
  ```
  package名(または `applicationId`)が分かれば
  `adb shell monkey -p <applicationId> -c android.intent.category.LAUNCHER 1` で起動できる旨を伝える
- 失敗: ステップ7へ

### ステップ7: 失敗診断(ローカルLLM)

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: その旨を伝え、通常通り自分でログを読んで
  診断する(ブロッカーにしない)
- 使える場合:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/android_log_review.py /tmp/android_install.log
  ```
  出力された原因・修正案をそのままユーザーに提示する(自分の言葉で書き直さない)。

## 注意

- 既定モデルは `gemma4:12b`。変更は環境変数 `LOCAL_REVIEW_MODEL`
- `INSTALL_FAILED_*`(署名不一致、旧バージョンとの競合など)もログ診断の対象になる
- 診断は参考情報(偽陽性あり得る)。最終的な修正判断は人間が行う
