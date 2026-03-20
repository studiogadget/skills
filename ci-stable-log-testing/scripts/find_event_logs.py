"""CI環境で安定動作するstructlogログ検証ヘルパー。

このファイルをテストモジュールにコピーして使用する。
プロジェクトのテストユーティリティとして共通化しても良い。

使用例:
    from structlog.testing import capture_logs

    def test_my_feature(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.clear()
        caplog.set_level(logging.WARNING)
        with capture_logs() as cap:
            my_function()

        logs = _find_event_logs(cap, event="my_event", caplog=caplog)
        assert len(logs) >= 1
        assert logs[0]["log_level"] == "warning"
"""

import re
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# ANSI正規化
# ---------------------------------------------------------------------------

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
_EVENT_KEY_VALUE_RE = re.compile(r"(?<!\w)event=(\"[^\"]*\"|'[^']*'|[^\s,}]+)")


def _normalize_log_message(message: str) -> str:
    """ANSIエスケープを除去し、key=value比較しやすい形へ正規化する。"""
    normalized = _ANSI_ESCAPE_RE.sub("", message)
    normalized = re.sub(r"\s*=\s*", "=", normalized)
    return normalized


def _contains_exact_event(message: str, event: str) -> bool:
    """event キーが指定値に完全一致するか判定する。"""
    for match in _EVENT_KEY_VALUE_RE.finditer(message):
        value = match.group(1).strip("\"'")
        if value == event:
            return True
    return False


def _collect_fallback_logs(
    *,
    event: str,
    caplog: pytest.LogCaptureFixture,
    include_exc_info: bool,
) -> list[dict[str, Any]]:
    """caplog から event の完全一致レコードを抽出する。"""
    fallback: list[dict[str, Any]] = []
    for record in caplog.records:
        msg = _normalize_log_message(record.getMessage())
        raw = _normalize_log_message(str(record.msg))
        msg_matches = _contains_exact_event(msg, event)
        raw_matches = _contains_exact_event(raw, event)
        if not (msg_matches or raw_matches):
            continue

        merged = msg if msg_matches else raw
        entry: dict[str, Any] = {
            "event": event,
            "log_level": record.levelname.lower(),
            "message": merged,
        }
        if include_exc_info:
            entry["exc_info"] = record.exc_info is not None or "Traceback (most recent call last):" in merged
        fallback.append(entry)
    return fallback


# ---------------------------------------------------------------------------
# フォールバック付きログ抽出
# ---------------------------------------------------------------------------


def _find_event_logs(
    captured: list[dict[str, Any]],
    *,
    event: str,
    caplog: pytest.LogCaptureFixture,
) -> list[dict[str, Any]]:
    """capture_logs にヒットがあれば structured のみ、空の場合のみ caplog をフォールバックとして使用する。

    structured が1件以上ある場合は caplog を参照せず、重複エントリの混入を防ぐ。
    structured が空の場合（CI環境でプロセッサーチェーンが動作しないケース等）に限り
    caplog から event キー完全一致のレコードを抽出する。

    Args:
        captured: structlog.testing.capture_logs() の戻り値
        event: 検索対象のイベント名（structlogの event キー）
        caplog: pytest の LogCaptureFixture

    Returns:
        マッチしたログエントリのリスト。構造化パスでは元のdictを、
        フォールバックパスでは event/log_level/message キーを持つdictを返す。
    """
    # 1) capture_logs の構造化パス（優先）
    structured = [e for e in captured if e.get("event") == event]
    if structured:
        return structured

    # 2) structured が空の場合のみ caplog フォールバック
    return _collect_fallback_logs(event=event, caplog=caplog, include_exc_info=False)


# ---------------------------------------------------------------------------
# exc_info付きバリアント（エラーログ検証用）
# ---------------------------------------------------------------------------


def _find_event_logs_with_exc_info(
    captured: list[dict[str, Any]],
    *,
    event: str,
    caplog: pytest.LogCaptureFixture,
) -> list[dict[str, Any]]:
    """_find_event_logs の exc_info 判定付きバリアント。

    ERRORログの exc_info=True 検証が必要な場合に使用する。
    structured が取れている場合は structured のみ返す（caplog との重複結合によるフレーキー防止）。
    structured が空の場合のみ caplog フォールバックで exc_info を付加して返す。
    """
    # 1) capture_logs の構造化パス（優先）
    structured = [e for e in captured if e.get("event") == event]
    if structured:
        return structured

    # 2) structured が空の場合のみ caplog フォールバック
    return _collect_fallback_logs(event=event, caplog=caplog, include_exc_info=True)
