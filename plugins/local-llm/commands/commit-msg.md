---
allowed-tools: Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*), Bash(git diff --cached*), Bash(git add *), Bash(git commit *)
description: ステージ済みの変更からコミットメッセージをローカルLLMで生成する(クラウド利用枠を消費しない)
user-invocable: true
---

# commit-msg: コミットメッセージ生成(ローカルLLM)

ステージ済みの git diff から、コミットメッセージをローカルLLM(Ollama)で生成する。

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない場合: Ollamaが起動していない。`brew services start ollama` を案内して終了する
- モデル一覧に `gemma4:12b` が無い場合: `ollama pull gemma4:12b` を案内して終了する

### ステップ2: ステージ確認

`git diff --cached --stat` が空なら、`git add` を促して終了する。

### ステップ3: 生成

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/commit_msg.py
```

### ステップ4: 提示・確定

- 生成されたメッセージ案をそのままユーザーに提示する
- 自分(Claude)の言葉で書き直さない(それではローカルLLMを使う意味がなくなる)
- ユーザーが承認したら `git commit -m "<メッセージ>"` を実行する(未承認のまま勝手にコミットしない)

## 注意

- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b)
