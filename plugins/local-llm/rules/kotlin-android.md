# Kotlin / Android セキュリティ・品質レビュー観点

外部入力(Intent の extras・Uri、Deep Link、WebView からの呼び出し、ContentProvider、
ネットワークレスポンス、ユーザー入力)が届き得る箇所を特に注意して確認する。

## データ保護

- 秘密情報(APIキー・トークン・パスワード)のハードコード、`BuildConfig` や `strings.xml` への平文埋め込み
- 認証トークン・個人情報を `SharedPreferences` に平文保存(`EncryptedSharedPreferences` / Keystore)
- 外部ストレージ(`getExternalFilesDir`, `MODE_WORLD_READABLE`)への機密データ保存
- `Log.d` / `Log.e` / `println` / Timber へのトークン・個人情報・レスポンス全文の出力
- SQLite / Room のクエリを文字列連結で組み立てていないか(`rawQuery` の引数バインド、`@Query` のパラメータ)

## コンポーネント・Intent

- `exported="true"` な Activity / Service / Receiver / Provider に権限やバリデーションが無い
- Implicit Intent で機密データを送っていないか(明示的 Intent / `setPackage`)
- `PendingIntent` に `FLAG_IMMUTABLE` が無い、`FLAG_MUTABLE` の根拠
- Deep Link / `intent.data` / `getStringExtra` の値を検証せずにパス・URL・SQL に使っていないか
- `startActivity(Intent.parseUri(userInput))` のような外部入力からの Intent 生成

## WebView

- `settings.javaScriptEnabled = true` + `addJavascriptInterface` の公開範囲
- `setAllowFileAccess` / `setAllowUniversalAccessFromFileURLs` の有効化
- `loadUrl(externalInput)` でスキーム・ホストを検証していない
- `WebViewClient.onReceivedSslError` で `proceed()` を呼んでいる(TLS 検証無効化)

## ネットワーク

- `cleartextTrafficPermitted="true"` / `http://` の URL
- `TrustManager` / `HostnameVerifier` を全許可にしている、`OkHttpClient` の `hostnameVerifier { _, _ -> true }`
- 証明書ピンニングの解除やデバッグ用設定のリリースビルドへの残留

## 暗号・乱数

- `java.util.Random` をトークン・鍵・ID 生成に使用(`SecureRandom`)
- MD5 / SHA-1 / ECB モード / 固定 IV / ハードコードされた鍵
- Keystore を使わず鍵をコードやファイルに保存

## 品質・並行処理

- 例外の握りつぶし(`catch (e: Exception) {}`、`runCatching { }.getOrNull()` の結果を無視)
- `GlobalScope.launch` / ライフサイクルに紐づかない CoroutineScope(リーク・クラッシュ)
- メインスレッドでのネットワーク・ディスク I/O(`Dispatchers.IO` を使う)
- `!!` による非 null 強制(外部入力・nullable な API 戻り値に対して)
- Context のリーク(Activity を static / ViewModel / シングルトンに保持)
- `Cursor` / `InputStream` / `FileDescriptor` のクローズ漏れ(`use { }` を使う)

## レビューの姿勢

- 差分(+の行)に現れたコードのみ対象。既存コードの問題は指摘しない
- 「外部入力が届くか不明」な場合は confidence を low にし、その旨を issue に書く
- スタイルの好み・ktlint / Android Lint で検出できる事項は指摘しない

## 判定例(few-shot)

指摘すべき例:

```kotlin
+        prefs.edit().putString("auth_token", token).apply()
```
→ category「データ保護」: 認証トークンを平文の SharedPreferences に保存している。
`EncryptedSharedPreferences` または Keystore で保護する。confidence: high

指摘してはいけない例(偽陽性):

```kotlin
+        val id = intent.getIntExtra(EXTRA_ID, -1).takeIf { it >= 0 } ?: return finish()
```
→ 値を検証しているので指摘しない。
