---
allowed-tools: Bash(python3 *), Bash(ollama list*), Read
description: 長いログ・CI出力・diff・文書をローカルLLMで要約する(クラウド利用枠を消費しない)
user-invocable: true
args:
  - name: file
    description: "入力ファイル(- で標準入力)。続けて --mode log|ci|diff|text、--lines N、--question '...' を渡せる"
    required: true
---

# summarize: 要約(ローカルLLM)

長いテキストを読んで要点を抜き出すだけの作業を、クラウドではなくローカルLLM(Ollama)で行う。
入力の種類(ログ / CI出力 / diff / 文書)は自動判定し、長い入力は分割→統合で要約する。

## 実行手順

### ステップ1: 前提確認

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ollama_health.py
```

- 接続できない、または `gemma4:12b` が無い場合: その旨を伝え、通常通り自分で読む(ブロッカーにしない)

### ステップ2: 実行

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/summarize.py $ARGUMENTS
```

例:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/summarize.py build.log --question "失敗したテストと原因"
git diff origin/main | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/summarize.py - --mode diff
```

### ステップ3: 結果の提示

- 出力の箇条書きをそのまま提示する(自分の言葉で書き直さない)
- 要約は入力に書かれていることだけを含む。判断や提案が必要なら、その部分だけを自分(Claude)が補う
