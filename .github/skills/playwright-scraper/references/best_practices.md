# Playwrightスクレイピング - ベストプラクティス

## 1. ログイン待機のパターン

### アンチパターン（危険）
```python
# ❌ sleep で固定待機（不安定）
import time
page.click("#login_button")
time.sleep(5)  # 5秒待つだけでは不十分
```

### 推奨パターン
```python
# ✅ ページロード完了まで待機
page.click("#login_button")
page.wait_for_load_state("networkidle")  # ネットワークリクエスト完了

# または、特定要素の出現を待機
page.wait_for_selector("#welcome_message", timeout=10000)  # 10秒
```

**レベル別選択**:
- `"load"`: DOM が構築され実行。最速だが不完全な場合も
- `"domcontentloaded"`: DOM 完全構築。標準的
- `"networkidle"`: ネットワークリクエスト全て完了。最も確実（遅い可能性）

## 2. ページネーション実装パターン

### 次ページリンクをループ
```python
page_count = 0
while page_count < max_pages:
    # 現在ページのデータ取得
    items = page.query_selector_all(".item")
    for item in items:
        # スクレイピング処理
        pass

    # 次ページリンク検査
    next_button = page.query_selector("a.next")
    if not next_button:
        break  # 次ページなし

    next_button.click()
    page.wait_for_load_state("networkidle")
    page_count += 1
```

### 推奨: URL パターンを予測して遷移
```python
# URLが規則的な場合（例: ?page=2, ?page=3 等）
for page_num in range(1, max_pages + 1):
    page.goto(f"{base_url}?page={page_num}")
    page.wait_for_load_state("networkidle")
    # スクレイピング処理
```

## 3. ダウンロード処理パターン

### 安全なダウンロード実装
```python
from pathlib import Path

# 1. ダウンロードハンドラを事前登録（クリック前）
download_path = Path("./downloads")
download_path.mkdir(exist_ok=True)

downloaded_file = None

def handle_download(download):
    nonlocal downloaded_file
    # ダウンロード完了後のファイルパス
    downloaded_file = download
    download.save_as(download_path / download.suggested_filename)

page.on("download", handle_download)

# 2. ダウンロードリンクをクリック
page.click("a[href*='zip']")

# 3. ダウンロード完了を待機
page.wait_for_load_state("networkidle")

if downloaded_file:
    print(f"Downloaded: {downloaded_file.suggested_filename}")
else:
    raise RuntimeError("Download did not start")
```

## 4. エラーハンドリング・リトライパターン

### タイムアウト対応
```python
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

max_retries = 3
for attempt in range(max_retries):
    try:
        page.wait_for_selector("#login_form", timeout=5000)
        break
    except PlaywrightTimeoutError:
        if attempt < max_retries - 1:
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
            page.reload()
        else:
            logger.error("Max retries exceeded", exc_info=True)
            raise
```

### セレクタ見つからず対応
```python
# セレクタが存在しないかチェック
element = page.query_selector("#expected_element")
if not element:
    raise ValueError(
        f"Expected element '#expected_element' not found. "
        f"Page title: {page.title()}, URL: {page.url}"
    )
```

## 5. 構造化ログ実装

### JSON ログで記録（推奨）
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

handler = logging.FileHandler("scrape.log")
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# ログ出力例
logger.info("Login started", extra={"url": page.url, "user": "***masked***"})
logger.error("Selector not found", extra={"selector": "#login"}, exc_info=True)
```

## 6. セレクタ検出・検証

### Playwright Inspector でセレクタ検証
```bash
PWDEBUG=1 python your_script.py
```
インスペクタ上で対話的にセレクタをテスト可能。

### ページソース解析でセレクタ候補を自動抽出
スキル付属の `scripts/selector_detector.py` を使用。

```bash
python scripts/selector_detector.py page.html --output selectors.json
```

## 7. 認証情報・シークレット管理

### 環境変数での参照
```python
import os
from dotenv import load_dotenv

load_dotenv()  # .env から読み込み

email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")

if not email or not password:
    raise EnvironmentError("Missing required environment variables: EMAIL, PASSWORD")

# パスワードはログに出力しない（マスク化）
logger.debug(f"Login attempt", extra={"user": email, "masked_pass": "***"})
```

### .env ファイル（ローカル開発専用）
```
EMAIL=your_email@example.com
PASSWORD=your_password_here
```

**.gitignore に追加**:
```
.env
.env.local
*.zip  # ダウンロード済みファイル
downloads/
```

## 8. パフォーマンス最適化

### 不要なリソース読み込み抑止
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        "./browser_data",
        ignore_https_errors=True,
        extra_http_headers={
            "User-Agent": "Custom Agent"
        }
    )
    page = context.new_page()

    # 画像・スタイル読み込み無効（スピード重視）
    page.route("**/*.{png,jpg,css}", lambda route: route.abort())
    page.goto("https://...")
```

### Headless モード（推奨・本番環境）
```python
browser = p.chromium.launch(headless=True)  # GUI 非表示、高速
```

### Headed モード（デバッグ時のみ）
```python
browser = p.chromium.launch(headless=False)  # ブラウザ表示
```

## 9. よくある落とし穴

| 落とし穴 | 原因 | 回避策 |
|---------|------|--------|
| Stale element error | DOM 更新後に古い要素参照 | 要素参照を毎回再取得 |
| Shadow DOM 内要素が見つからない | CSS セレクタが shadow DOM を貫通できない | `page.locator()` 使用 or XPath調整 |
| Cookie 喪失 | ブラウザクローズで Cookie 消失 | Persistent Context 使用 |
| Popup/Dialog 未対応 | `dialog` / `popup` を明示的に待機せず | `page.on("popup", ...)` 登録 |

## 10. テスト統合例

Pytest でのスクレイピング機能テスト:

```python
# tests/test_scraper.py
import pytest
from your_scraper import GenericScraper

@pytest.fixture
def scraper():
    return GenericScraper()

def test_login_success(scraper):
    """ログイン成功を検証"""
    result = scraper.login("test@example.com", "password123")
    assert result is True

def test_download_zip(scraper, tmp_path):
    """ZIPダウンロード成功を検証"""
    scraper.login("test@example.com", "password123")
    zip_file = scraper.download_data(save_path=tmp_path)
    assert zip_file.exists()
    assert zip_file.suffix == ".zip"
```
