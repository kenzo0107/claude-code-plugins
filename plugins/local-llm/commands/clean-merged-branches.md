---
allowed-tools: Bash(git status *), Bash(git branch *), Bash(git checkout *), Bash(git pull *)
description: main/develop以外のローカルブランチのうちgit branch -dで安全に削除できる(マージ済みの)ものをまとめて削除する
user-invocable: true
---

# clean-merged-branches: マージ済みローカルブランチの一括削除

`main` / `master` / `develop` を除くローカルブランチのうち、マージ済みで
`git branch -d`(force ではない安全な削除)が成功するものだけをまとめて削除する。

`-d` は未マージのブランチには失敗するため、作業中のブランチを誤って消すことはない。
**`-D`(force delete)は使用しない。**

## 保護対象ブランチ

- `main`
- `master`
- `develop`
- 現在チェックアウト中のブランチ

## 実行手順

### 1. 作業ツリーの状態確認

```bash
git status --porcelain
```

未コミットの変更がある場合は、ユーザーに知らせて続行してよいか確認する(stashやcommitを促す)。
マージ判定は現在のHEAD基準で行われるため、勝手に `main` へcheckoutしたり `git pull` したりしない。
ユーザーが「mainの最新を基準にしたい」と言った場合のみ、確認の上で `git checkout main && git pull` を行う。

### 2. 削除候補の洗い出しと安全削除

```bash
current=$(git branch --show-current)
for b in $(git branch --format='%(refname:short)' | grep -vE "^(main|master|develop|${current})$"); do
  if git branch -d "$b" 2>/dev/null; then
    echo "deleted: $b"
  else
    echo "skipped (unmerged or protected): $b"
  fi
done
```

### 3. 結果報告

削除したブランチ一覧と、未マージのためスキップしたブランチ一覧をユーザーに簡潔に報告する。
スキップしたブランチを削除したい場合は、ユーザーに `git branch -D <branch>` の実行意思を
明示的に確認してから行う(無断でforce deleteしない)。
