# Playwrightスクレイピング - ベストプラクティス

## 1. ログイン待機のパターン

### アンチパターン（危険）
```python
# ❌ sleep で固定待機（不安定）
import time
page.get_by_role("button", name="ログイン").click()
time.sleep(5)  # 固定待機は不要。Locatorが自動待機する
```

### 推奨パターン（Locator）
```python
# ✅ Locatorは操作前に自動で要素が操作可能になるまで待機する
page.get_by_label("メールアドレス").fill(email)
page.get_by_label("パスワード").fill(password)
page.get_by_role("button", name="ログイン").click()

# ページ遷移を伴う場合はload_stateで追加待機
page.wait_for_load_state("networkidle")

# または、ログイン完了を示す特定要素をLocatorで待機
page.get_by_text("ようこそ").wait_for(state="visible")
```

**`wait_for_load_state` レベル別選択**:
- `"load"`: DOM が構築され実行。最速だが不完全な場合も
- `"domcontentloaded"`: DOM 完全構築。標準的
- `"networkidle"`: ネットワークリクエスト全て完了。最も確実（遅い可能性）

## 2. ページネーション実装パターン

### 推奨: Locatorで次ページリンクをループ
```python
page_count = 0
while page_count < max_pages:
    # 現在ページのデータ取得（Locatorで全要素を取得）
    for item in page.locator(".item").all():
        name = item.locator(".name").text_content()
        # スクレイピング処理

    # 次ページLocatorで存在確認
    next_btn = page.get_by_role("link", name="次へ")
    if not next_btn.is_visible():
        break  # 次ページなし

    next_btn.click()
    page.wait_for_load_state("networkidle")
    page_count += 1
```

### 複数セレクタ候補がある場合: `locator.or_()`
```python
# ✅ 複数のセレクタ候補を宣言的に記述（query_selectorのループ不要）
next_btn = page.get_by_role("link", name="次へ").or_(
    page.locator("a.pagination-next")
).or_(
    page.locator("button[aria-label='Next page']")
)

if next_btn.is_visible():
    next_btn.click()
```

### URLパターンが規則的な場合
```python
for page_num in range(1, max_pages + 1):
    page.goto(f"{base_url}?page={page_num}")
    page.wait_for_load_state("networkidle")
    # スクレイピング処理
```

## 3. ダウンロード処理パターン

### 安全なダウンロード実装（Locatorでクリック）
```python
from pathlib import Path

download_path = Path("./downloads")
download_path.mkdir(exist_ok=True)

downloaded_file = None

def handle_download(download):
    nonlocal downloaded_file
    downloaded_file = download
    download.save_as(download_path / download.suggested_filename)

page.on("download", handle_download)

# ✅ Locatorでダウンロードリンクをクリック
page.get_by_role("link", name="ダウンロード").click()

# ダウンロード完了を待機（download.path()がブロック）
if downloaded_file:
    _ = downloaded_file.path()  # 完了まで待機
    print(f"Downloaded: {downloaded_file.suggested_filename}")
else:
    raise RuntimeError("Download did not start")
```

## 4. エラーハンドリング・リトライパターン

### タイムアウト対応（Locator）
```python
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

max_retries = 3
for attempt in range(max_retries):
    try:
        # Locatorのwait_forでタイムアウト設定
        page.get_by_css("#login_form").wait_for(state="visible", timeout=5000)
        break
    except PlaywrightTimeoutError:
        if attempt < max_retries - 1:
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
            page.reload()
        else:
            logger.error("Max retries exceeded", exc_info=True)
            raise
```

### Locator見つからず対応
```python
# Locatorのis_visible()でチェック（query_selectorのNone判定不要）
target = page.get_by_role("region", name="データ一覧")
if not target.is_visible():
    raise ValueError(
        f"Expected element 'データ一覧' not found. "
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
logger.error("Locator not found", extra={"locator": "get_by_role('link', name='次へ')"}, exc_info=True)
```

## 6. Locator検出・検証

### Playwright Inspector でLocator検証
```bash
PWDEBUG=1 python your_script.py
```
インスペクタ上でLocatorを対話的にテスト可能。`Pick locator` ボタンで要素クリック → Locatorコードを自動生成。

### ページソース解析でロケーター候補を自動抽出
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
logger.debug("Login attempt", extra={"user": email, "masked_pass": "***"})
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
        extra_http_headers={"User-Agent": "Custom Agent"}
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
| Stale element error | DOM 更新後に古い要素参照 | Locator使用（自動リトライ） |
| Shadow DOM 内要素が見つからない | CSS セレクタが shadow DOM を貫通できない | `page.locator()` はデフォルトで貫通 |
| Cookie 喪失 | ブラウザクローズで Cookie 消失 | Persistent Context 使用 |
| Popup/Dialog 未対応 | `dialog` / `popup` を明示的に待機せず | `page.on("popup", ...)` 登録 |
| 複数セレクタ候補の管理が煩雑 | `query_selector` のループが必要 | `locator.or_()` で宣言的に記述 |

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
