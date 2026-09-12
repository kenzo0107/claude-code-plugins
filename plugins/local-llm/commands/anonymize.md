---
allowed-tools: Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*), Read
description: ログ・テキストの個人情報(メール・IP・電話・人名等)をローカルでマスクする。クラウドLLMに渡す前の前処理
user-invocable: true
args:
  - name: file
    description: "入力ファイル。- で標準入力"
    required: true
---

# anonymize: 個人情報マスキング(ローカル)

ログやテキストをクラウドLLM(Claude)に渡す前に、個人情報をローカルでマスクする。
正規表現(メール・IP・電話番号)で確実に取れるものを機械的に置換し、人名など文脈依存のものは
ローカルLLMに「列挙だけ」させてコード側で置換する。最後に正規表現で再走査し、漏れ疑いがあれば exit 2。

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない、または `gemma4:12b` が無い場合: その旨を伝えて終了する(マスク無しでクラウドに渡さない)

### ステップ2: 実行

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/anonymize.py $ARGUMENTS
```

- `<入力>.masked.<拡張子>` と変換表 `<出力>.map.json` が生成される
- exit 2 の場合はマスク漏れの疑いがある。stderr の警告を提示し、該当箇所を人が確認するまでクラウドに渡さない

### ステップ3: 結果の提示

- 置換件数と出力パスを提示する
- **変換表(.map.json)は個人情報そのもの**なので、内容を読み上げたり、他のツールの入力に含めたりしない
- 以降の分析でクラウドに渡すのはマスク済みファイルだけにする

## 注意

- 正規表現のパターンは日本の固定・携帯電話番号(ハイフン区切り)を前提。他形式は LLM 検出に依存する
- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b)
