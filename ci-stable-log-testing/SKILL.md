---
name: ci-stable-log-testing
description: "CI環境で安定動作するPythonテスト（特にstructlogのログ検証）を書く際に使用。「CIで失敗する」「capture_logsが不安定」「ログアサーションがCIだけ落ちる」「caplogフォールバック」「ANSI混入」「xdistでログが取れない」という課題で起動。capture_logs→caplogフォールバック→ANSI正規化→アサーション設計の流れで堅牢なテストを書く。"
---

# CI-Stable Test: structlogログ検証の安定化パターン

## 背景と問題

`structlog.testing.capture_logs()` はローカルでは動作するが、CI環境（特にpytest-xdist並列実行、GitHub Actions ubuntu runner）では以下の理由でログが取得できないことがある。

1. **モジュールレベルのロガーキャッシュ**: 先行テストがロガーをバインド済みだと `capture_logs()` のコンテキストマネージャがログを捕捉できない
2. **pytest-xdist並列実行**: ワーカー間でstructlogのグローバル設定が競合する
3. **caplogメッセージのANSI混入**: CI環境のstructlogレンダラがANSIエスケープ付きで出力し、`key=value` の単純一致が崩れる
4. **exc_info の表現差異**: CI環境では `record.exc_info` が `None` でもメッセージ本文にTracebackが含まれる場合がある

## 解決パターン: 2段階フォールバック

### パターン概要

```
capture_logs() で構造化ログを取得
 ├── 取得成功 → 構造化dictで厳密アサーション
 └── 取得失敗（空リスト）→ caplog にフォールバック
      └── ANSIエスケープ除去 + key=value正規化してアサーション
```

### 実装手順

#### Step 1: ANSI正規化ユーティリティを定義

```python
import re

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

def _normalize_log_message(message: str) -> str:
    """ANSIエスケープを除去し、key=value比較しやすい形へ正規化する。"""
    normalized = _ANSI_ESCAPE_RE.sub("", message)
    normalized = re.sub(r"\s*=\s*", "=", normalized)
    return normalized
```

#### Step 2: フォールバック付きログ抽出ヘルパーを定義

```python
def _find_event_logs(
    captured: list[dict[str, object]],
    *,
    event: str,
    caplog: pytest.LogCaptureFixture,
) -> list[dict[str, object]]:
    """capture_logs の結果が空の場合に caplog をフォールバック利用する。"""
    structured = [e for e in captured if e.get("event") == event]
    if structured:
        return structured

    fallback: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in caplog.records:
        msg = _normalize_log_message(record.getMessage())
        raw = _normalize_log_message(str(record.msg))
        if event in msg or event in raw:
            merged = msg if event in msg else raw
            if merged in seen:
                continue
            seen.add(merged)
            fallback.append({
                "event": event,
                "log_level": record.levelname.lower(),
                "message": merged,
            })
    return fallback
```

**設計判断**:
- `seen` セットで重複メッセージを除外（capture_logsとcaplog両方に同じログが流れるケースへの対策）
- `record.msg`（フォーマット前）も確認する（ハンドラチェーンによる差異を吸収）

#### Step 3: テスト関数でcaplogを併用

```python
@pytest.mark.asyncio
async def test_example(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.clear()
    caplog.set_level(logging.WARNING)  # 対象ログレベルに合わせる
    with capture_logs() as cap:
        await some_function()

    logs = _find_event_logs(cap, event="my_event", caplog=caplog)
    assert len(logs) >= 1
```

#### Step 4: アサーションの分岐パターン

```python
log_entry = logs[0]
assert log_entry["log_level"] == "warning"

# 構造化パス（capture_logs成功時）はキーで直接検証
if "detail_key" in log_entry:
    assert log_entry["detail_key"] == expected_value
else:
    # フォールバックパス: 正規化済みメッセージでkey=value検証
    assert "detail_key=expected_value" in log_entry["message"]
```

## 判断チェックリスト

テストでstructlogのログ検証を書く際、以下に該当すれば本パターンを適用する。

- [ ] `structlog.testing.capture_logs()` でログを検証している
- [ ] CI（GitHub Actions等）でのみテストが失敗する
- [ ] pytest-xdist（`-n auto`）で並列実行している
- [ ] ログメッセージの `key=value` 部分文字列でアサーションしている

## exc_info の検証

CI環境では `record.exc_info` が `None` でもメッセージ本文にTracebackが埋め込まれることがある。

```python
fallback.append({
    # ...
    "exc_info": (
        record.exc_info is not None
        or "Traceback (most recent call last):" in merged
    ),
})
```

## 件数アサーションの注意

CI環境ではハンドラチェーンの差異によりログが複数回記録されることがある。

- **`== 1` よりも `>= 1` を推奨**（特にフォールバックパスで）
- 複数件を許容する場合は `logs[-1]`（最後のエントリ）で検証すると安定する
- `seen` セットによる重複除外を入れても、formatter差異で完全一致しない場合がある

## やらないこと（スコープ外）

- ログの出力順序の厳密な検証（CI環境では保証されない）
- structlog自体の設定変更やモンキーパッチ
- caplogだけに依存する方式（構造化ログのキーアクセスが失われる）
- プロダクションコードの変更（テスト側のみで吸収する）

## 参照

- [references/troubleshooting.md](references/troubleshooting.md): CI環境でよくある失敗パターンと対処法
- [scripts/find_event_logs.py](scripts/find_event_logs.py): コピー用のヘルパー関数テンプレート
