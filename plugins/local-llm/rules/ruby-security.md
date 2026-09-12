# Ruby / Rails 一般セキュリティ・品質レビュー観点

外部入力(`params`、リクエストヘッダ、Cookie、環境変数、ファイル内容、外部APIレスポンス)が
届き得る箇所を特に注意して確認する。

## インジェクション

- SQL: `where("name = '#{params[:name]}'")` のような文字列補間・`find_by_sql` / `execute` /
  `order(params[:sort])` / `pluck(params[:col])` への外部入力(プレースホルダ `?` / ハッシュ条件 /
  `sanitize_sql_*` / 許可リストを使う)
- OSコマンド: バッククォート・`system("... #{x}")`・`Kernel#exec`・`IO.popen`・`Open3` に文字列で
  外部入力を連結していないか(配列形式で引数分離する)
- パストラバーサル: `File.read(params[:path])`・`send_file(Rails.root.join("files", params[:name]))`
  など、外部入力をパスに使って検証していないか
- `eval` / `instance_eval` / `send(params[:method])` / `constantize` / `safe_constantize` への外部入力
- `Marshal.load` / `YAML.load`(`safe_load` でない)/ `JSON.load` への外部入力
- 正規表現: `Regexp.new(params[:q])`(ReDoS)、`^` `$` による行単位マッチ(`\A` `\z` を使う)

## Rails 固有

- Strong Parameters の欠落・`permit!`・`params.permit(...)` の過剰許可(`admin`, `role` など)
- Mass Assignment: `update(params[:user])` のように permit していないハッシュを渡していないか
- 認可の欠落(IDOR): `Model.find(params[:id])` で操作者の所有・権限を確認していないか
  (`current_user.posts.find` のようにスコープする)
- `html_safe` / `raw` / `<%== %>` への外部入力(XSS)。`sanitize` の許可タグ
- `redirect_to params[:url]`(オープンリダイレクト。`allow_other_host: false` や許可リスト)
- CSRF: `protect_from_forgery` の除外(`skip_before_action :verify_authenticity_token`)の根拠
- `render inline:`・`render params[:template]` への外部入力
- `Rails.logger` / 例外メッセージへのパスワード・トークン・個人情報の出力(`filter_parameters`)
- `config.force_ssl` の無効化、Cookie の `secure` / `httponly` 欠落
- ファイルアップロード: Content-Type・拡張子・サイズの検証、公開ディレクトリへの保存

## 秘密情報

- APIキー・パスワード・トークンのハードコード(`credentials` / 環境変数を使う)
- 秘密情報や個人情報をログ・例外・レスポンスに含めていないか

## 外部リクエスト・SSRF

- `Net::HTTP.get(URI(params[:url]))`・`open-uri` の `URI.open`(`open` との混同を含む)への外部入力
- TLS 検証の無効化(`verify_mode = OpenSSL::SSL::VERIFY_NONE`)

## 暗号・乱数

- パスワードハッシュに `Digest::MD5` / `SHA1` / 単純な SHA256(`has_secure_password` / bcrypt を使う)
- トークン生成に `rand` / `Random`(`SecureRandom` を使う)
- 認証情報の比較に `==`(`ActiveSupport::SecurityUtils.secure_compare`)

## 入力検証・リソース

- サイズ無制限の読み込み(`request.body.read`、巨大ファイルの `File.read`)
- N+1 や無制限の `all` / `each` による大量ロード(`find_each`, `limit`)
- zip/tar 展開時のパス検証(Zip Slip)

## エラーハンドリング(品質)

- `rescue => e` / `rescue Exception` で握りつぶす(`rescue nil` を含む)
- `rescue Exception`(`Interrupt` / `SystemExit` まで捕まえる)
- トランザクション外での複数モデル更新、`update_column` / `update_all` によるバリデーション・コールバック回避の根拠

## レビューの姿勢

- 差分(+の行)に現れたコードのみ対象。既存コードの問題は指摘しない
- 「外部入力が届くか不明」な場合は confidence を low にし、その旨を issue に書く
- スタイルの好み・RuboCop で検出できる事項は指摘しない

## 判定例(few-shot)

指摘すべき例:

```ruby
+    @users = User.where("name LIKE '%#{params[:q]}%'")
```
→ category「インジェクション」: 文字列補間による SQL インジェクション。
`User.where("name LIKE ?", "%#{User.sanitize_sql_like(params[:q])}%")` にする。confidence: high

指摘してはいけない例(偽陽性):

```ruby
+    @post = current_user.posts.find(params[:id])
```
→ current_user でスコープされているので IDOR ではない。
