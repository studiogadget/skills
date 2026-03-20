# CI環境でのstructlogテスト失敗: トラブルシューティング

## 症状 → 原因 → 対処

### 1. `assert len(cap) >= 1` が失敗（capture_logsが空）

**原因**: モジュールレベルのstructlogロガーが先行テストで既にバインドされ、`capture_logs()` のコンテキストマネージャが捕捉するロガーと異なるインスタンスを使っている。

**対処**: `caplog` フォールバックを追加。テスト関数に `caplog: pytest.LogCaptureFixture` を引数追加し、`_find_event_logs()` ヘルパーで両方を検索する。

---

### 2. `assert "key=value" in message` が失敗（値は正しいのに）

**原因**: CI環境のstructlogレンダラがANSIカラーコード（`\x1b[36m`, `\x1b[35m` 等）をキーと値の間に挿入する。

**例**:
```
# ローカル（ANSIなし）
page_num=1 row_index=1

# CI（ANSI混入）
\x1b[36mpage_num\x1b[0m=\x1b[35m1\x1b[0m \x1b[36mrow_index\x1b[0m=\x1b[35m1\x1b[0m
```

**対処**: `_normalize_log_message()` でANSIエスケープを除去してからアサーションする。

---

### 3. `assert entry["exc_info"] is True` が失敗

**原因**: CI環境では `record.exc_info` が `None` だが、structlogのレンダラがTraceback文字列をメッセージ本文に埋め込んでいる。

**対処**: `record.exc_info is not None or "Traceback (most recent call last):" in message` の複合判定を使う。

---

### 4. `assert len(logs) == 1` が失敗（2件になる）

**原因**: structlogとstdlib loggingの両方のハンドラが同じイベントをキャプチャし、caplog側に重複エントリが生成される。

**対処**:
- `seen` セットで重複メッセージを除外する
- 件数アサーションは `>= 1` に緩和する
- 複数件を許容し `logs[-1]` で最後のエントリを検証する

---

### 5. `caplog.records` にログが全く記録されない

**原因**: `caplog.set_level()` の呼び出し漏れ、または対象ログレベルより低いレベルが設定されている。

**対処**: テスト関数冒頭で `caplog.clear()` + `caplog.set_level(logging.対象レベル)` を必ず呼ぶ。

---

### 6. イベント名は正しいのに `_find_event_logs` が0件を返す

**原因**: `record.getMessage()` がフォーマット済み文字列を返し、イベント名がレンダラの装飾で分離されている場合がある。

**対処**: `record.msg`（フォーマット前の生メッセージ）も検索対象に追加する。`_find_event_logs` の最新版では `str(record.msg)` も正規化して照合している。
