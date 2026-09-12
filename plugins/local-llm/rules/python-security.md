# Python 一般セキュリティ・品質レビュー観点

外部入力(CLI引数、環境変数、ファイル内容、subprocess の出力、ネットワーク経由の値)が
届き得る箇所を特に注意して確認する。

## インジェクション

- OSコマンド: `subprocess` に `shell=True` + 変数、または `os.system` / `os.popen` への
  未検証の外部入力がないか
- SQL: クエリを f-string / `%` / `.format` で組み立てていないか(パラメータ化クエリを使うこと)
- パストラバーサル: ユーザー入力をそのまま `open()` / `Path()` に渡していないか
  (`..` を含むパスの正規化・許可ディレクトリ配下であることの検証)
- `eval` / `exec` / `pickle.loads` に外部入力(ファイル内容・ネットワーク経由データ)を渡していないか
- `yaml.load`(`safe_load` でない)への外部入力

## 秘密情報

- APIキー・パスワード・トークンのハードコード
- 秘密情報や個人情報を `print` / ログ / 例外メッセージに出力していないか
- `.gitignore` されるべきファイル(`.env`, 認証情報, 変換表等)を誤って読み書き・出力していないか

## 外部リクエスト・SSRF

- ユーザー入力のURLへ `requests` / `urllib` でアクセスしていないか(内部ネットワークへの到達可能性)
- TLS検証の無効化(`verify=False`)

## 入力検証・リソース

- サイズ無制限の読み込み(巨大ファイル・巨大レスポンスを丸ごとメモリに載せていないか)
- zip/tar 展開時のパス検証(Zip Slip)
- 一時ファイルの安全でない作成(`tempfile` を使わず固定パス+競合の可能性)

## エラーハンドリング(品質)

- 例外の握りつぶし(`except: pass`、`except Exception: pass`)
- `with` を使わないファイル/ソケットのクローズ漏れ
- サブプロセスの戻り値・エラー出力を確認していない(`check=True` なし、stderr 無視)

## レビューの姿勢

- 差分(+の行)に現れたコードのみ対象。既存コードの問題は指摘しない
- 「外部入力が届くか不明」な場合は confidence を low にし、その旨を issue に書く
- スタイルの好み・フォーマッタ(black/ruff)で検出できる事項は指摘しない

## 判定例(few-shot)

指摘すべき例(見逃しやすい):

```python
+def read_upload(user_path: str) -> bytes:
+    with open(os.path.join(UPLOAD_DIR, user_path), "rb") as f:
```
→ category「インジェクション」: `os.path.join` は `user_path` が絶対パスや `..` を含むと
UPLOAD_DIR の外を開ける(パストラバーサル)。`Path(UPLOAD_DIR, user_path).resolve()` が
UPLOAD_DIR 配下にあることを検証する。confidence: high(引数名が外部入力を示している)

```python
+def load_cache(path: str):
+    with open(path, "rb") as f:
+        return pickle.load(f)
```
→ category「インジェクション」: `pickle.load` は内容次第で任意コード実行になる。`path` の出所は差分から
読めないが、危険 API の無防備な使用なので指摘する。confidence: low(呼び出し元の入力次第と明記)

指摘してはいけない例(偽陽性):

```python
+    cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
```
→ パラメータ化されているので SQL インジェクションではない。「user_id が文字列なら…」のような
仮定での指摘はしない。
