#!/usr/bin/env python3
"""VS Code Chat Export(JSON) を Read サイズに収まる形に縮約するフィルタ。

想定入力:
- VS Code のコマンド `Chat: Export Chat...` で出力した JSON ファイル
- もしくはそれらをまとめたディレクトリ（*.json を走査）

出力:
- JSONL（1行=1リクエスト）で、パターン抽出に必要な最小限の情報だけを残す。
  - toolCallResults 等の巨大フィールドは破棄
  - prompt/response はトリム可能
  - 可能なら timestamp/workspace/sessionId を抽出

注意:
- エクスポート JSON の内部スキーマは VS Code / 拡張の更新で変わり得る。
  このスクリプトは「観測例」に基づく best-effort で、フィールド有無に応じてフォールバックする。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
from pathlib import Path
from typing import Any

NOISE_PATTERNS = [
    # VS Code / Copilot が付けるシステム文言っぽいもの
    r"^The current date is\s+",
    r"^No tasks or terminals found\.",
    r"^No tasks found\.",
    r"^I'll (now )?update\s+",  # 例: "I'll update the PRD..."
    # ありがちな Claude Code / Copilot の開始宣言
    r"^作業を開始します",
    r"^わかりました",
]


# ざっくりした秘匿情報マスク（完全ではない）
REDACTIONS: list[tuple[re.Pattern, str]] = [
    # GitHub token
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "ghp_[REDACTED]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "github_pat_[REDACTED]"),
    # OpenAI API key (古い形式含む)
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "sk-[REDACTED]"),
    # AWS access key id
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AKIA[REDACTED]"),
    # Google API key (ざっくり)
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "AIza[REDACTED]"),
    # Private key block
    (
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY]",
    ),
]


def _apply_redactions(text: str) -> str:
    out = text
    for pat, repl in REDACTIONS:
        out = pat.sub(repl, out)
    return out


def _as_millis(ts: Any) -> int | None:
    """ts をミリ秒 Unix に寄せる。"""
    if ts is None:
        return None
    if isinstance(ts, bool):
        return None
    if isinstance(ts, int | float):
        # 10桁(秒) / 13桁(ミリ秒) をざっくり判定
        if ts > 10_000_000_000:  # 13桁相当
            return int(ts)
        return int(ts * 1000)
    if isinstance(ts, str):
        # ISO8601 っぽい文字列
        try:
            # 末尾Z/オフセットを許容
            dt_obj = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return int(dt_obj.timestamp() * 1000)
        except Exception:
            return None
    return None


def _now_millis() -> int:
    return int(dt.datetime.now(dt.UTC).timestamp() * 1000)


def _within_days(ts_ms: int | None, days: int | None) -> bool:
    if days is None or ts_ms is None:
        return True
    cutoff = _now_millis() - days * 24 * 60 * 60 * 1000
    return ts_ms >= cutoff


def _match_any(patterns: list[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in patterns)


def _compile_noise_patterns(extra: list[str] | None = None) -> list[re.Pattern]:
    pats = list(NOISE_PATTERNS)
    if extra:
        pats.extend(extra)
    return [re.compile(p) for p in pats]


def _iter_input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob("*.json") if p.is_file()])
    raise FileNotFoundError(str(input_path))


def _safe_get(d: Any, path: list[str]) -> Any:
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _extract_timestamp(req: dict[str, Any]) -> int | None:
    # 観測例: req.result.metadata.timestamp
    for candidate in [
        _safe_get(req, ["result", "metadata", "timestamp"]),
        req.get("timestamp"),
    ]:
        ts = _as_millis(candidate)
        if ts is not None:
            return ts
    return None


def _extract_workspace(req: dict[str, Any]) -> str | None:
    # 観測例: req.result.metadata.renderedUserMessage[].baseUri.path
    rendered = _safe_get(req, ["result", "metadata", "renderedUserMessage"])
    if isinstance(rendered, list):
        for item in rendered:
            if isinstance(item, dict):
                base_uri = item.get("baseUri")
                if isinstance(base_uri, dict):
                    path = base_uri.get("path")
                    if isinstance(path, str) and path:
                        return path
    # フォールバック: response 内の baseUri
    resp = req.get("response")
    if isinstance(resp, list):
        for item in resp:
            if isinstance(item, dict):
                base_uri = item.get("baseUri")
                if isinstance(base_uri, dict):
                    path = base_uri.get("path")
                    if isinstance(path, str) and path:
                        return path
    return None


def _extract_session_id(req: dict[str, Any]) -> str | None:
    # 観測例: req.result.metadata.modelMessageId/sessionId もしくは response 内
    for candidate in [
        _safe_get(req, ["result", "metadata", "sessionId"]),
        req.get("sessionId"),
    ]:
        if isinstance(candidate, str) and candidate:
            return candidate
    resp = req.get("response")
    if isinstance(resp, list):
        for item in resp:
            if isinstance(item, dict):
                sid = item.get("sessionId")
                if isinstance(sid, str) and sid:
                    return sid
    return None


def _extract_tools(req: dict[str, Any]) -> list[str]:
    tools: list[str] = []

    # message.toolCalls
    msg = req.get("message")
    if isinstance(msg, dict):
        tool_calls = msg.get("toolCalls")
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if isinstance(tc, dict):
                    name = tc.get("name") or tc.get("toolName")
                    if isinstance(name, str) and name:
                        tools.append(name)

    resp = req.get("response")
    if isinstance(resp, list):
        for item in resp:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "prepareToolInvocation":
                name = item.get("toolName")
                if isinstance(name, str) and name:
                    tools.append(name)
            elif kind == "toolInvocationSerialized":
                # toolId だけでも残す（後で相関を取る場合に便利）
                tool_id = item.get("toolId")
                if isinstance(tool_id, str) and tool_id:
                    tools.append(tool_id)

    # 重複除去（順序保持）
    seen = set()
    uniq: list[str] = []
    for t in tools:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def _extract_text_blocks(req: dict[str, Any]) -> tuple[str, str]:
    """(user_text, assistant_text)"""
    user_text = ""
    msg = req.get("message")
    if isinstance(msg, dict):
        t = msg.get("text")
        if isinstance(t, str):
            user_text = t

    assistant_parts: list[str] = []
    resp = req.get("response")
    if isinstance(resp, list):
        for item in resp:
            if not isinstance(item, dict):
                continue
            # 文字列 value を拾う。toolログ/進捗は除外（必要なら --keep-tool-logs）
            val = item.get("value")
            if isinstance(val, str) and val.strip():
                assistant_parts.append(val)

    assistant_text = "\n".join(assistant_parts)
    return user_text, assistant_text


def _trim(text: str, max_chars: int | None) -> str:
    if max_chars is None:
        return text
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Export JSON ファイル、または JSON を含むディレクトリ")
    ap.add_argument("--workspace", default=None, help="workspace（baseUri.path）部分一致フィルタ")
    ap.add_argument("--days", type=int, default=None, help="timestamp がある場合の過去 N 日フィルタ")
    ap.add_argument(
        "--keyword", action="append", default=[], help="user/assistant どちらかに含まれる必要があるキーワード（複数可）"
    )
    ap.add_argument(
        "--exclude", action="append", default=[], help="user/assistant どちらかに含まれると除外するキーワード（複数可）"
    )
    ap.add_argument("--max-turns", type=int, default=None, help="最大出力ターン数（古い順に間引き）")
    ap.add_argument("--max-prompt-chars", type=int, default=4000, help="user_text の最大文字数")
    ap.add_argument("--max-assistant-chars", type=int, default=8000, help="assistant_text の最大文字数")
    ap.add_argument("--noise-filter", action="store_true", help="ノイズ（定型文）っぽいものを軽く除外")
    ap.add_argument("--no-redact", action="store_true", help="秘匿情報のマスクを無効化")
    return ap.parse_args()


def main() -> None:
    args = _parse_args()

    input_path = Path(args.input).expanduser().resolve()
    files = _iter_input_files(input_path)

    noise_res = _compile_noise_patterns()
    out_rows: list[dict[str, Any]] = []

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            # JSON が壊れてる/別形式の場合はスキップ
            logging.error(f"Failed to parse JSON from {f}: {e}")
            continue

        requests = data.get("requests")
        if not isinstance(requests, list):
            continue

        for idx, req in enumerate(requests):
            if not isinstance(req, dict):
                continue

            ts_ms = _extract_timestamp(req)
            if not _within_days(ts_ms, args.days):
                continue

            workspace = _extract_workspace(req)
            if args.workspace and (not workspace or args.workspace not in workspace):
                continue

            session_id = _extract_session_id(req)
            tools = _extract_tools(req)
            user_text, assistant_text = _extract_text_blocks(req)

            if args.noise_filter and user_text and _match_any(noise_res, user_text.strip()):
                continue

            # include/exclude keyword filters
            hay = (user_text or "") + "\n" + (assistant_text or "")
            if args.keyword and not any(k in hay for k in args.keyword):
                continue
            if args.exclude and any(k in hay for k in args.exclude):
                continue

            if not args.no_redact:
                user_text = _apply_redactions(user_text)
                assistant_text = _apply_redactions(assistant_text)

            user_text = _trim(user_text, args.max_prompt_chars)
            assistant_text = _trim(assistant_text, args.max_assistant_chars)

            out_rows.append(
                {
                    "source": "vscode-chat-export",
                    "file": str(f),
                    "index": idx,
                    "timestamp": ts_ms,
                    "workspace": workspace,
                    "sessionId": session_id,
                    "prompt": user_text,
                    "response": assistant_text,
                    "tools": tools,
                }
            )

    # timestamp があれば昇順で並べる。なければ (file, index) 順。
    out_rows.sort(key=lambda r: (r["timestamp"] is None, r["timestamp"] or 0, r["file"], r["index"]))

    if args.max_turns is not None and len(out_rows) > args.max_turns:
        out_rows = out_rows[-args.max_turns :]

    for row in out_rows:
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
