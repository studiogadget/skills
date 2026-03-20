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


def _normalize_log_message(message: str) -> str:
    """ANSIエスケープを除去し、key=value比較しやすい形へ正規化する。"""
    normalized = _ANSI_ESCAPE_RE.sub("", message)
    normalized = re.sub(r"\s*=\s*", "=", normalized)
    return normalized


# ---------------------------------------------------------------------------
# フォールバック付きログ抽出
# ---------------------------------------------------------------------------


def _find_event_logs(
    captured: list[dict[str, Any]],
    *,
    event: str,
    caplog: pytest.LogCaptureFixture,
) -> list[dict[str, Any]]:
    """capture_logs の結果が空の場合に caplog をフォールバック利用する。

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

    # 2) caplog フォールバックパス
    fallback: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in caplog.records:
        msg = _normalize_log_message(record.getMessage())
        raw = _normalize_log_message(str(record.msg))
        if event in msg or event in raw:
            merged = msg if event in msg else raw
            if merged in seen:
                continue
            seen.add(merged)
            fallback.append(
                {
                    "event": event,
                    "log_level": record.levelname.lower(),
                    "message": merged,
                }
            )
    return fallback


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
    """
    structured = [e for e in captured if e.get("event") == event]
    if structured:
        return structured

    fallback: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in caplog.records:
        msg = _normalize_log_message(record.getMessage())
        raw = _normalize_log_message(str(record.msg))
        if event in msg or event in raw:
            merged = msg if event in msg else raw
            if merged in seen:
                continue
            seen.add(merged)
            fallback.append(
                {
                    "event": event,
                    "log_level": record.levelname.lower(),
                    "message": merged,
                    "exc_info": (record.exc_info is not None or "Traceback (most recent call last):" in merged),
                }
            )
    return fallback
