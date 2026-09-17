#!/usr/bin/env python3
"""Ollama の接続確認とモデル存在確認(curl 代替)。

スキル/コマンドの「前提確認」ステップで使う。curl は利用環境の permissions.deny
(`Bash(curl:*)`)で拒否されることがあるため、標準ライブラリのみで確認する。

使い方:
  python3 ollama_health.py [MODEL ...]

終了コード:
  0: 接続でき、指定モデル(省略時は DEFAULT_MODEL)がすべて存在する
  1: Ollama に接続できない
  2: 接続はできるが指定モデルが無い
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ollama_client as oc  # noqa: E402


def main(argv: list[str]) -> int:
    wanted = argv or [oc.DEFAULT_MODEL]
    models = oc.available_models()
    if models is None:
        print(f"NG: Ollama に接続できません ({oc.OLLAMA_URL})。`brew services start ollama` を確認してください")
        return 1
    missing = [m for m in wanted if m not in models and f"{m}:latest" not in models]
    print(f"OK: Ollama 接続 ({oc.OLLAMA_URL}) / モデル {len(models)} 件: {', '.join(sorted(models))}")
    if missing:
        print(f"NG: モデルが見つかりません: {', '.join(missing)}。`ollama pull <model>` を実行してください")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
