#!/usr/bin/env python3
"""ローカルLLM(Ollama)ツール群の共通クライアント。

全スクリプトがここを通ることで、以下を一箇所で担保する:
  - モデルの存在確認と代替モデルへのフォールバック
  - system/user メッセージ分離と出力形式の再掲(長い入力での指示忘れ対策)
  - JSON Schema による出力の構造強制(format=schema)
  - 入力量に応じた num_ctx の自動拡張(切り捨ての回避)
  - diff のノイズ除去・ファイル単位分割(大きな差分の分割処理)
  - 実行統計(prompt/output トークン数・所要秒)の取得

依存は標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

OLLAMA_URL = os.environ.get("LOCAL_LLM_OLLAMA_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("LOCAL_LLM_DEFAULT_MODEL", "gemma4:12b")
STRONG_MODEL = os.environ.get("LOCAL_LLM_STRONG_MODEL", "qwen3.6:27b")
MIN_NUM_CTX = 16384
MAX_NUM_CTX = int(os.environ.get("LOCAL_LLM_MAX_NUM_CTX", "32768"))
# これを超える差分はファイル単位に分割して処理する(≒ 7〜8k トークン)
MAX_CHUNK_CHARS = int(os.environ.get("LOCAL_LLM_MAX_CHUNK_CHARS", "24000"))
THINK = os.environ.get("LOCAL_LLM_THINK", "0") == "1"
QUIET = os.environ.get("LOCAL_LLM_QUIET", "0") == "1"


class OllamaError(RuntimeError):
    pass


def log(msg: str) -> None:
    if not QUIET:
        print(msg, file=sys.stderr, flush=True)


# ---------------- モデル解決 ----------------


def available_models() -> set[str] | None:
    """インストール済みモデル名の集合。Ollama に接続できなければ None。"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as res:
            return {m["name"] for m in json.loads(res.read()).get("models", [])}
    except (urllib.error.URLError, OSError, ValueError):
        return None


def resolve_model(preferred: str, *fallbacks: str) -> str:
    """preferred が無ければ fallbacks の順に存在するものを返す。どれも無ければ例外。"""
    models = available_models()
    if models is None:
        raise OllamaError(f"Ollama に接続できません ({OLLAMA_URL})。`brew services start ollama` を確認してください")
    for m in (preferred, *fallbacks):
        if m in models or f"{m}:latest" in models:
            if m != preferred:
                log(f"[local-llm] {preferred} が無いため {m} を使います")
            return m
    raise OllamaError(f"モデルが見つかりません: {preferred}。`ollama pull {preferred}` を実行してください")


# ---------------- トークン見積もり・num_ctx ----------------


def estimate_tokens(text: str) -> int:
    """粗い見積もり。コードは約3.5文字/トークン、日本語は約1.5文字/トークン。"""
    cjk = sum(1 for ch in text if ord(ch) > 0x2E80)
    other = len(text) - cjk
    return int(cjk / 1.5 + other / 3.5) + 1


def fit_num_ctx(prompt_text: str, reserve_output: int = 3000) -> int:
    """入力に対して余裕のある num_ctx を 4096 の倍数で選ぶ(下限 MIN、上限 MAX)。"""
    need = int(estimate_tokens(prompt_text) * 1.25) + reserve_output
    ctx = max(MIN_NUM_CTX, ((need + 4095) // 4096) * 4096)
    if ctx > MAX_NUM_CTX:
        log(f"[local-llm] 入力が大きすぎます(見積 {need} tok > num_ctx 上限 {MAX_NUM_CTX})。分割処理を推奨")
        ctx = MAX_NUM_CTX
    return ctx


# ---------------- チャット ----------------


def chat(
    messages: list[dict],
    model: str,
    *,
    schema: dict | None = None,
    temperature: float = 0.1,
    num_ctx: int | None = None,
    think: bool | None = None,
    timeout: int = 900,
    label: str = "",
) -> tuple[str, dict]:
    """Ollama /api/chat を呼び、(本文, 実行統計) を返す。

    schema を渡すと JSON Schema で出力を強制する(Ollama の structured outputs)。
    stream で受け取り、生成中の進捗を stderr に出す(tty のときのみ)。
    """
    prompt_text = "".join(m.get("content", "") for m in messages)
    ctx = num_ctx or fit_num_ctx(prompt_text)
    body: dict = {
        "model": model,
        "stream": True,
        "think": THINK if think is None else think,
        "options": {"temperature": temperature, "num_ctx": ctx},
        "messages": messages,
    }
    if schema is not None:
        body["format"] = schema
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    show = sys.stderr.isatty() and not QUIET
    tag = f"[{label or model}]"
    started = time.monotonic()
    parts: list[str] = []
    final: dict = {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            for line in res:
                chunk = json.loads(line)
                if "error" in chunk:
                    raise OllamaError(chunk["error"])
                parts.append(chunk.get("message", {}).get("content", ""))
                if show and len(parts) % 20 == 0:
                    print(f"\r{tag} 生成中 {len(parts)} tok {time.monotonic() - started:.0f}s", end="", file=sys.stderr, flush=True)
                if chunk.get("done"):
                    final = chunk
    except urllib.error.URLError as e:
        raise OllamaError(f"Ollama に接続できません: {e}") from e
    if show:
        print("\r" + " " * 60 + "\r", end="", file=sys.stderr, flush=True)
    stats = {
        "model": model,
        "num_ctx": ctx,
        "prompt_tokens": final.get("prompt_eval_count"),
        "output_tokens": final.get("eval_count"),
        "duration_s": round(final.get("total_duration", 0) / 1e9, 1),
    }
    if stats["prompt_tokens"] and stats["prompt_tokens"] >= ctx * 0.95:
        log(f"[local-llm] 警告: prompt {stats['prompt_tokens']} tok が num_ctx {ctx} に張り付いています(入力切り捨ての疑い)")
    return "".join(parts).strip(), stats


def chat_json(messages: list[dict], model: str, schema: dict, **kw) -> tuple[dict, dict]:
    """JSON を返すチャット。パースに失敗したら1回だけ再生成する。"""
    content, stats = chat(messages, model, schema=schema, **kw)
    try:
        return json.loads(content), stats
    except json.JSONDecodeError:
        log("[local-llm] JSON パース失敗。再生成します")
        content, stats2 = chat(messages, model, schema=schema, **kw)
        stats2["retried"] = True
        return json.loads(content), stats2


def merge_stats(stats_list: list[dict]) -> dict:
    """分割実行した複数回の統計を1つにまとめる(トークンと秒は合計、chunks に回数)。"""
    if len(stats_list) == 1:
        return stats_list[0]
    return {
        "model": stats_list[0]["model"],
        "num_ctx": max(s["num_ctx"] for s in stats_list),
        "prompt_tokens": sum(s.get("prompt_tokens") or 0 for s in stats_list),
        "output_tokens": sum(s.get("output_tokens") or 0 for s in stats_list),
        "duration_s": round(sum(s["duration_s"] for s in stats_list), 1),
        "chunks": len(stats_list),
    }


# ---------------- diff の前処理 ----------------

# レビュー・要約の対象にしない(ノイズになる)ファイル
NOISE_PATTERNS = [
    r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Gemfile\.lock|poetry\.lock|uv\.lock|Cargo\.lock|go\.sum|composer\.lock|Podfile\.lock)$",
    r"(^|/)\.terraform\.lock\.hcl$",
    r"\.(min\.js|min\.css|map|svg|png|jpe?g|gif|ico|webp|pdf|woff2?|ttf|eot)$",
    r"(^|/)(vendor|node_modules|dist|build|\.terraform)/",
    r"\.pb\.go$|_generated\.|\.generated\.|(^|/)generated/",
    r"(^|/)__snapshots__/",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS))


@dataclass
class FileDiff:
    path: str
    text: str  # "diff --git" から次のファイルの直前まで

    @property
    def added(self) -> int:
        return sum(1 for l in self.text.splitlines() if l.startswith("+") and not l.startswith("+++"))

    @property
    def removed(self) -> int:
        return sum(1 for l in self.text.splitlines() if l.startswith("-") and not l.startswith("---"))

    @property
    def is_binary(self) -> bool:
        return "Binary files" in self.text or "GIT binary patch" in self.text


_HEADER_RE = re.compile(r"^diff --git (?:a/)?(\S+) (?:b/)?(\S+)", re.M)


def split_diff(diff: str) -> list[FileDiff]:
    """unified diff をファイル単位に分割する。"""
    starts = [m.start() for m in _HEADER_RE.finditer(diff)]
    if not starts:
        return [FileDiff("(unknown)", diff)] if diff.strip() else []
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(diff)
        text = diff[s:e]
        m = _HEADER_RE.match(text)
        out.append(FileDiff(m.group(2), text))
    return out


def filter_diff(files: list[FileDiff], exts: tuple[str, ...] | None = None) -> tuple[list[FileDiff], list[str]]:
    """ノイズファイル・バイナリを除外し、exts 指定時はその拡張子だけ残す。(残り, 除外したパス)"""
    kept, skipped = [], []
    for f in files:
        if f.is_binary or NOISE_RE.search(f.path) or (exts and not f.path.endswith(exts)):
            skipped.append(f.path)
        else:
            kept.append(f)
    return kept, skipped


def diff_stat(files: list[FileDiff]) -> str:
    """`git diff --stat` 相当の一覧。分割処理の統合段階で全体像を渡すために使う。"""
    return "\n".join(f"{f.path}  (+{f.added} -{f.removed})" for f in files)


def chunk_files(files: list[FileDiff], max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """ファイル群を max_chars 以下のチャンクにまとめる。1ファイルで超える場合はハンク単位で割る。"""
    chunks: list[str] = []
    cur: list[str] = []
    size = 0
    for f in files:
        if len(f.text) > max_chars:
            if cur:
                chunks.append("".join(cur))
                cur, size = [], 0
            chunks.extend(_split_hunks(f, max_chars))
            continue
        if size + len(f.text) > max_chars and cur:
            chunks.append("".join(cur))
            cur, size = [], 0
        cur.append(f.text)
        size += len(f.text)
    if cur:
        chunks.append("".join(cur))
    return chunks


def _split_hunks(f: FileDiff, max_chars: int) -> list[str]:
    parts = re.split(r"(?m)^(?=@@ )", f.text)
    header, hunks = parts[0], parts[1:]
    out, cur = [], header
    for h in hunks:
        if len(cur) + len(h) > max_chars and cur != header:
            out.append(cur)
            cur = header
        cur += h
    if cur != header:
        out.append(cur)
    return out or [f.text[:max_chars]]


def prepare_diff(diff: str, exts: tuple[str, ...] | None = None) -> tuple[list[str], str, list[str]]:
    """diff → (チャンク一覧, stat 文字列, 除外パス)。全ツール共通の前処理。"""
    files, skipped = filter_diff(split_diff(diff), exts)
    return chunk_files(files), diff_stat(files), skipped


# ---------------- プロンプト組み立て ----------------


def build_messages(system: str, user: str, restate: str = "") -> list[dict]:
    """system に役割と規約、user に入力を置き、規約の要点を入力の後ろに再掲する。

    長い入力の後ろで先頭の指示を失う現象(evals の ctx-probe)への対策。
    """
    if restate:
        user = f"{user}\n\n---\n{restate}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
