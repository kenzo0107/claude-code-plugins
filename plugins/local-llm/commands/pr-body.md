---
allowed-tools: Bash(python3 *), Bash(curl -s http://localhost:11434/*), Bash(ollama list*), Bash(git diff *), Bash(git branch *), Bash(gh pr create *), Bash(gh repo view *)
description: ブランチ差分からPR本文(Summary/Test plan)をローカルLLMで生成する(クラウド利用枠を消費しない)
user-invocable: true
args:
  - name: base
    description: "比較先のgit ref (例: origin/main)。省略時はデフォルトブランチを自動判定"
    required: false
---

# pr-body: PR本文生成(ローカルLLM)

ベースブランチとの差分から、GitHub PRの本文(Summary/Test plan)をローカルLLM(Ollama)で生成する。

## 実行手順

### ステップ1: 前提確認

```bash
curl -s http://localhost:11434/api/tags
```

- 接続できない場合: Ollamaが起動していない。`brew services start ollama` を案内して終了する
- モデル一覧に `gemma4:12b` が無い場合: `ollama pull gemma4:12b` を案内して終了する

### ステップ2: base ref特定

`$ARGUMENTS` が指定されていればそれを使う。無ければ `gh repo view --json defaultBranchRef` 等で
デフォルトブランチを特定し、`origin/<デフォルトブランチ>` を base とする。

### ステップ3: 生成

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pr_body.py <base>
```

### ステップ4: 提示・確定

- 生成された本文(Summary/Test plan)をそのままユーザーに提示する
- 自分(Claude)の言葉で書き直さない(それではローカルLLMを使う意味がなくなる)。ただしTest planの
  チェック内容が明らかに実態と食い違う場合のみ修正してよい
- タイトルは短く安価なので、これまで通り自分で簡潔に作成してよい
- ユーザーが承認したら `gh pr create --title "<タイトル>" --body "<生成結果>"` を実行する

## 注意

- モデル変更: 環境変数 `LOCAL_REVIEW_MODEL`(既定: gemma4:12b)
