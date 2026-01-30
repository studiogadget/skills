# Playwright スクレイピング - 公式ドキュメント・リソース集

## 公式ドキュメント（最新）

### Playwright 本体
- **Getting Started**: https://playwright.dev/python/docs/intro
- **API Reference**: https://playwright.dev/python/docs/api/class-browser
- **Debugging Guide**: https://playwright.dev/python/docs/debug
- **Best Practices**: https://playwright.dev/python/docs/best-practices
- **GitHub Repository**: https://github.com/microsoft/playwright-python

### 主要API（スクレイピングで頻出）

#### Page オブジェクト
- `page.goto(url)`: URLに遷移
- `page.fill(selector, text)`: フォーム入力
- `page.click(selector)`: クリック
- `page.wait_for_load_state(state)`: ページ読み込み完了待機
- `page.wait_for_selector(selector, timeout)`: 要素出現待機
- `page.query_selector(selector)`: 単一要素取得
- `page.query_selector_all(selector)`: 複数要素取得
- `page.get_attribute(selector, name)`: 属性値取得
- `page.text_content(selector)`: テキスト取得

#### Download ハンドリング
- `page.on("download", handler)`: ダウンロード開始時コールバック登録
- `download.path()`: ダウンロード完了後のファイルパス取得
- `download.save_as(path)`: ダウンロードファイル保存（別パス）

#### セレクタ（CSS / XPath）
- CSS: `#id`, `.class`, `button[type='submit']`
- XPath: `//button[text()='Login']`, `//a[@href*='zip']`

## システム要件

- Python 3.8+（推奨 3.10以上）
- Playwright: `pip install playwright`
- ブラウザバイナリ: `playwright install chromium` （初回必須）

## セキュリティ・認証情報管理

### 環境変数での参照（推奨）
```python
import os
from dotenv import load_dotenv

load_dotenv()
email = os.environ["GMO_EMAIL"]
password = os.environ["GMO_PASSWORD"]
```

### .env ファイル（ローカル開発用）
```env
GMO_EMAIL=user@example.com
GMO_PASSWORD=secure_password_here
```

**注意**: `.env` は `.gitignore` に追加（シークレット情報を含むため）

## 非同期実装の選択肢

### 同期版（シンプル、推奨初心者向け）
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://...")
```

### 非同期版（複数ページ並列処理向け）
```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://...")

asyncio.run(main())
```

## ロギング・デバッグ

### Playwright デバッグモード
```bash
PWDEBUG=1 python script.py
```
Playwright Inspector を開いて、ステップ実行・セレクタ確認が可能。

### 構造化ログ（Python）
```python
import logging
import json

logger = logging.getLogger(__name__)

# JSON形式で記録
log_data = {
    "action": "login",
    "status": "success",
    "duration_ms": 1234,
    "timestamp": "2025-01-30T10:00:00Z"
}
logger.info(json.dumps(log_data))
```

## 一般的なトラブル

| 問題 | 原因 | 解決策 |
|------|------|--------|
| Timeout error | ページ読み込み遅延 | `wait_for_load_state()` タイムアウト増加、ネットワーク確認 |
| Selector not found | セレクタ誤指定 | PWDEBUG=1 で検査、HTML構造確認 |
| Download not started | ハンドラ未登録 | `page.on("download", ...)` をクリック前に登録 |
| 認証失敗 | 環境変数未設定 | `.env` 確認、認証情報の正確性確認 |

## コミュニティ・相談先

- **Issue Tracker**: https://github.com/microsoft/playwright-python/issues
- **Stack Overflow**: `[playwright]` タグ
- **Slack Community**: Playwrightコミュニティ（GitHub から参照可能）
