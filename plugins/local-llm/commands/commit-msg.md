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
- モデル一覧に `qwen3.6:27b` が無い場合: `ollama pull qwen3.6:27b` を案内して終了する

### ステップ2: ブランチ確認

```bash
git branch --show-current
```

- `main` または `master` の場合: そのままコミットしてよいか、別ブランチを作成するかをユーザーに確認する
  - 別ブランチを作成する場合: ブランチ名を確認し `git checkout -b <ブランチ名>` を実行してから続行する
  - main/masterのまま続行する場合: そのまま次のステップに進む

### ステップ3: ステージ確認

`git status --porcelain` で未ステージ・未追跡の変更を確認する。

- 変更があり未ステージなら `git add -A` でステージする(ユーザーに確認を取らず自動でステージしてよい)
- ステージ対象・未ステージの変更がいずれも無ければ、その旨を伝えて終了する

### ステップ4: 生成

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/commit_msg.py
```

### ステップ5: 提示・確定

- 生成されたメッセージ案をそのままユーザーに提示する
- 自分(Claude)の言葉で書き直さない(それではローカルLLMを使う意味がなくなる)
- ユーザーが承認したら `git commit -m "<メッセージ>"` を実行する(未承認のまま勝手にコミットしない)

## 注意

- 既定モデルは `qwen3.6:27b`(生成に数十秒)。精度検証の結果、`gemma4:12b` は複数の変更を
  含むdiffで箇条書きへの分解を誤ることがあったため、コミットメッセージはこちらを既定にしている
- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`
