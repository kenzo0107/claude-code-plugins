# TypeScript / JavaScript 一般セキュリティ・品質レビュー観点

フロントエンド・Node.js の両方を対象とする。外部入力(リクエストボディ・クエリ・ヘッダ・
URL・`location`・`postMessage`・外部APIレスポンス・環境変数)が届き得る箇所を特に注意して確認する。

## インジェクション

- XSS: `innerHTML` / `outerHTML` / `insertAdjacentHTML` / `document.write` / React の
  `dangerouslySetInnerHTML` / Vue の `v-html` への外部入力(サニタイズの有無)
- `eval` / `new Function` / `setTimeout(string)` / `vm.runInContext` への外部入力
- SQL / NoSQL: クエリの文字列連結・テンプレートリテラル、Mongo の `$where` や
  `{ [key]: value }` 形式で外部入力をオペレータ位置に置ける構造
- OSコマンド: `child_process.exec` / `execSync` に文字列で外部入力を連結(`execFile` / `spawn` で引数分離)
- パストラバーサル: `fs.readFile(path.join(base, userInput))`・`res.sendFile` で `..` や絶対パスの検証が無い
- プロトタイプ汚染: 外部入力を `Object.assign` / 再帰マージ / `obj[key] = value` で取り込む(`__proto__`)
- 正規表現: 外部入力からの `new RegExp`、ネストした量指定子(ReDoS)

## 認証・認可・セッション

- 認可チェックの欠落(IDOR): ID を受け取る API で操作者の権限確認が無い
- JWT: `algorithms` 未指定・`none` 許可・秘密鍵のハードコード・`verify` せず `decode` のみで信用
- Cookie の `httpOnly` / `secure` / `sameSite` 欠落
- CORS: `origin: '*'` や `Access-Control-Allow-Origin` に `req.headers.origin` をそのまま反射(credentials 付き)
- `postMessage` の `origin` 未検証、`window.open` の `noopener` 欠落
- オープンリダイレクト: `res.redirect(req.query.next)` を検証していない

## 秘密情報

- APIキー・トークンのハードコード、フロントエンドバンドルへの秘密情報の混入(`NEXT_PUBLIC_*`, `VITE_*` の誤用)
- `console.log` / ロガーへのトークン・個人情報・リクエスト全文の出力
- `.env` の誤コミット、`process.env` の値をレスポンスに含める

## 外部リクエスト・SSRF

- 外部入力の URL に `fetch` / `axios` / `http.get` でアクセス(内部ネットワーク到達性)
- TLS 検証の無効化(`rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`)

## 入力検証・リソース

- リクエストボディ・アップロードのサイズ上限が無い(`express.json({ limit })`, multer の `limits`)
- 外部入力をスキーマ検証(zod / yup / class-validator)せず型アサーション(`as`)で信用している
- 無制限の `Promise.all` による同時実行、無限ループの可能性がある `while`
- 依存パッケージの `postinstall` スクリプト・出所不明なパッケージの追加

## 型・品質

- `any` / `as unknown as` / `@ts-ignore` による型の抜け道(特に外部入力周り)
- `await` 忘れ(浮動 Promise)、`.catch` の無い Promise、`try/catch` で握りつぶし(`catch {}`)
- `==` による比較(`===` を使う)、`parseInt` の基数省略
- `useEffect` の依存配列漏れ・クリーンアップ漏れ(React)
- 非 null アサーション `!` の外部入力への適用

## レビューの姿勢

- 差分(+の行)に現れたコードのみ対象。既存コードの問題は指摘しない
- 「外部入力が届くか不明」な場合は confidence を low にし、その旨を issue に書く
- スタイルの好み・ESLint / Prettier / tsc で検出できる事項は指摘しない

## 判定例(few-shot)

指摘すべき例:

```ts
+  res.redirect(req.query.next as string);
```
→ category「認証・認可・セッション」: 外部入力への無検証リダイレクト(オープンリダイレクト)。
相対パスのみ許可するか許可リストと照合する。confidence: high

指摘してはいけない例(偽陽性):

```ts
+  const body = CreateUserSchema.parse(req.body);
```
→ zod でスキーマ検証しているので「型アサーションで信用」には当たらない。
