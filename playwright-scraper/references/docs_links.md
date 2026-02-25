# Playwright スクレイピング - 公式ドキュメント・リソース集

## 公式ドキュメント（最新）

### Playwright 本体
- **Getting Started**: https://playwright.dev/python/docs/intro
- **Locators（主要）**: https://playwright.dev/python/docs/locators
- **Best Practices**: https://playwright.dev/python/docs/best-practices
- **Debugging Guide**: https://playwright.dev/python/docs/debug
- **GitHub Repository**: https://github.com/microsoft/playwright-python

### 主要API（スクレイピングで頻出）

#### Locator オブジェクト（推奨: 全操作はLocator経由）
- https://playwright.dev/python/docs/api/class-locator
- `page.locator(selector)`: CSSセレクタでLocator生成
- `page.get_by_role(role, name=...)`: ロールベースLocator（最優先）
- `page.get_by_label(text)`: ラベルテキストでLocator生成
- `page.get_by_placeholder(text)`: プレースホルダーでLocator生成
- `page.get_by_text(text)`: 表示テキストでLocator生成
- `locator.fill(text)`: フォーム入力（自動待機付き）
- `locator.click()`: クリック（自動待機付き）
- `locator.wait_for(state=...)`: 指定状態まで待機
- `locator.text_content()`: テキスト取得
- `locator.get_attribute(name)`: 属性値取得
- `locator.all()`: マッチした全要素のLocatorリスト
- `locator.count()`: マッチ数取得
- `locator.is_visible()`: 表示状態チェック
- `locator.or_(other)`: 複数セレクタのいずれかにマッチ
- `locator.first` / `locator.nth(n)`: インデックス指定

#### Page オブジェクト
- https://playwright.dev/python/docs/api/class-page
- `page.goto(url)`: URLに遷移
- `page.wait_for_load_state(state)`: ページ読み込み完了待機
- `page.on("download", handler)`: ダウンロード開始時コールバック登録

#### Download ハンドリング
- **Downloads（公式ガイド）**: https://playwright.dev/python/docs/downloads
- `page.expect_download()`: ダウンロードイベントをコンテキストマネージャーで待機（推奨）
- `download.path()`: ダウンロード完了後のファイルパス取得（完了まで待機）
- `download.save_as(path)`: ダウンロードファイル保存（別パス）

#### Error クラス
- https://playwright.dev/python/docs/api/class-error
- `TimeoutError`: 操作タイムアウト
- `Error`: 汎用エラー基底クラス

> ⚠️ **非推奨 API（使用しない）**
> - `page.query_selector()` / `page.query_selector_all()` → `page.locator()` を使用
> - `page.fill()` / `page.click()` → `locator.fill()` / `locator.click()` を使用
> - `page.wait_for_selector()` → `locator.wait_for()` を使用

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
email = os.environ["EMAIL"]
password = os.environ["PASSWORD"]
```

### .env ファイル（ローカル開発用）
```env
EMAIL=user@example.com
PASSWORD=secure_password_here
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
    # Locator使用
    page.get_by_role("button", name="ログイン").click()
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
        # Locator使用（awaitが必要）
        await page.get_by_role("button", name="ログイン").click()

asyncio.run(main())
```

## ロギング・デバッグ

### Playwright デバッグモード
```bash
PWDEBUG=1 python script.py
```
Playwright Inspector を開いて、ステップ実行・Locator確認が可能。

### 構造化ログ（Python）
```python
import logging
import json

logger = logging.getLogger(__name__)
```
