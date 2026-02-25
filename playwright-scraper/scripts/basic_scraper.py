#!/usr/bin/env python3
"""
Basic Playwright Scraper Example

ログイン認証・ページネーション・ダウンロード機能を実装した
基本的なスクレイピング例。Locatorを中心に実装。

使用方法:
    python basic_scraper.py

依存:
    - playwright
    - python-dotenv
"""

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Playwright インポート
try:
    from playwright.sync_api import Locator, sync_playwright
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Error: playwright not installed. Run: pip install playwright")
    sys.exit(1)

# ロギング設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PlaywrightScraper:
    """Playwrightベースのスクレイパー基底クラス（Locator中心）"""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000, download_dir: str | None = None) -> None:
        """
        初期化。

        Args:
            headless: ヘッドレスモード（GUI非表示）
            timeout_ms: タイムアウト時間（ミリ秒）
            download_dir: ダウンロード保存先ディレクトリ
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.download_dir = Path(download_dir or "./downloads")
        self.download_dir.mkdir(exist_ok=True, parents=True)

        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    def launch(self) -> None:
        """ブラウザ起動"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout_ms)
            logger.info("Browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)
            raise

    def close(self) -> None:
        """ブラウザ終了"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")

    def login(
        self,
        url: str,
        email_locator: str | None = None,
        password_locator: str | None = None,
        login_button_locator: str | None = None,
        email: str = "",
        password: str = "",  # nosec B107:空文字列デフォルト値は実際のセキュリティリスクではない
        success_locator: str | None = None,
    ) -> bool:
        """
        ログイン処理（汎用・Locatorベース）。

        Locatorは操作前に自動で要素が操作可能になるまで待機するため、
        `wait_for_selector` による手動待機は不要。

        Args:
            url: ログインページURL
            email_locator: メールアドレス入力フィールドのCSSセレクタ（省略時: get_by_label使用）
            password_locator: パスワード入力フィールドのCSSセレクタ（省略時: get_by_label使用）
            login_button_locator: ログインボタンのCSSセレクタ（省略時: get_by_role使用）
            email: ログインメールアドレス（環境変数や引数から）
            password: ログインパスワード（環境変数や引数から）
            success_locator: ログイン完了を検証するCSSセレクタ（省略可）

        Returns:
            ログイン成功時 True

        Raises:
            PlaywrightTimeoutError: タイムアウト
        """
        try:
            logger.info(f"Navigating to {url}")
            self.page.goto(url)
            self.page.wait_for_load_state("domcontentloaded")

            # メールアドレス入力（Locatorが自動待機）
            email_loc: Locator = (
                self.page.locator(email_locator) if email_locator else self.page.get_by_label("メールアドレス")
            )
            logger.debug("Filling email field")
            email_loc.fill(email)

            # パスワード入力（Locatorが自動待機）
            password_loc: Locator = (
                self.page.locator(password_locator) if password_locator else self.page.get_by_label("パスワード")
            )
            logger.debug("Filling password field")
            password_loc.fill(password)

            # ログインボタン クリック（Locatorが自動待機）
            login_btn: Locator = (
                self.page.locator(login_button_locator)
                if login_button_locator
                else self.page.get_by_role("button", name="ログイン")
            )
            logger.info("Clicking login button")
            login_btn.click()

            # ページロード完了を待機
            self.page.wait_for_load_state("networkidle")
            logger.info("Login page loaded after click")

            # ログイン完了を検証（オプション）
            if success_locator:
                self.page.locator(success_locator).wait_for(state="visible", timeout=self.timeout_ms)
                logger.info(f"Login verification locator found: {success_locator}")

            logger.info("Login successful")
            return True

        except PlaywrightTimeoutError as e:
            logger.error(f"Login timeout (success locator: {success_locator})", exc_info=True)
            raise ValueError(
                f"ログイン処理がタイムアウト。パスワード確認、ロケーターを確認してください。"
                f" (URL: {url}, success_locator: {success_locator})"
            ) from e
        except Exception:
            logger.error("Login failed", exc_info=True)
            raise

    def download_file(
        self,
        link_locator: str | None = None,
        link_name: str | None = None,
        expected_filename_pattern: str | None = None,
    ) -> Path | None:
        """
        ファイルダウンロード処理（Locator + download.path()パターン）。

        Locatorでリンクをクリックし、download.path() でダウンロード完了を確実に待機。

        Args:
            link_locator: ダウンロードリンク/ボタンのCSSセレクタ（link_nameより優先）
            link_name: ダウンロードリンクのアクセシブル名（get_by_role使用）
            expected_filename_pattern: 期待するファイル名パターン（チェック用、オプション）

        Returns:
            ダウンロードディレクトリ内のファイルパス

        Raises:
            RuntimeError: ダウンロード失敗（イベント未発生またはpath()失敗）
            PlaywrightTimeoutError: ロケーター見つからずまたはタイムアウト
        """
        downloaded_file: Any = None

        def handle_download(download: Any) -> None:
            nonlocal downloaded_file
            downloaded_file = download
            logger.debug(f"Download event received: {download.suggested_filename}")

        try:
            # ダウンロードハンドラを登録（クリック前）
            self.page.on("download", handle_download)

            # Locatorでダウンロードリンクをクリック
            if link_locator:
                loc: Locator = self.page.locator(link_locator)
            elif link_name:
                loc = self.page.get_by_role("link", name=link_name)
            else:
                raise ValueError("link_locator または link_name を指定してください")

            logger.info(f"Clicking download link (locator: {link_locator or link_name!r})")
            loc.click()

            # ダウンロード開始を確認
            if not downloaded_file:
                raise RuntimeError(
                    f"Download did not start (no download event). Locator: {link_locator or link_name!r}"
                )

            # ダウンロード完了を待機（Playwright標準パターン）
            # download.path() はダウンロードが完全に完了するまでブロック
            temp_file_path = Path(downloaded_file.path())

            # ダウンロードディレクトリに保存
            target_path = self.download_dir / downloaded_file.suggested_filename
            shutil.copy2(temp_file_path, target_path)

            logger.info(f"Download completed: {downloaded_file.suggested_filename} -> {target_path}")
            return target_path

        except RuntimeError:
            logger.error("Download failed: event not received", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Download failed: {e!s}", exc_info=True)
            raise RuntimeError(
                f"Download completion wait failed. Expected file: {expected_filename_pattern or 'unknown'}. Error: {e}"
            ) from e
        finally:
            self.page.remove_listener("download", handle_download)

    def get_text(self, css_selector: str) -> str:
        """
        Locator経由でテキストを取得。

        Args:
            css_selector: CSSセレクタ

        Returns:
            テキスト内容

        Raises:
            ValueError: ロケーターが見つからず
        """
        try:
            loc = self.page.locator(css_selector)
            loc.wait_for(state="visible", timeout=self.timeout_ms)
            text = loc.text_content()
            if text is None:
                raise ValueError(f"Element text is None. Locator: {css_selector!r}, URL: {self.page.url}")
            return text.strip()
        except PlaywrightTimeoutError:
            logger.error(f"Locator not found: {css_selector!r}", exc_info=True)
            raise
        except Exception:
            logger.error(f"Failed to get text from {css_selector!r}", exc_info=True)
            raise

    def get_attribute(self, css_selector: str, attr: str) -> str | None:
        """
        Locator経由で属性値を取得。

        Args:
            css_selector: CSSセレクタ
            attr: 属性名

        Returns:
            属性値（存在しない場合 None）
        """
        try:
            return self.page.locator(css_selector).get_attribute(attr)
        except Exception:
            logger.warning(f"Failed to get attribute {attr!r} from {css_selector!r}", exc_info=True)
            return None


# 使用例
if __name__ == "__main__":
    # 環境変数読み込み
    load_dotenv()

    EMAIL = os.environ.get("EMAIL", "your_email@example.com")
    PASSWORD = os.environ.get("PASSWORD", "your_password")

    scraper = None
    try:
        scraper = PlaywrightScraper(headless=True, download_dir="./downloads")
        scraper.launch()

        # ログイン（Locatorベース）
        scraper.login(
            url="https://example.com/login",  # 実際のURLに置き換えてください
            email=EMAIL,
            password=PASSWORD,
            success_locator=".welcome-message",  # ログイン完了を検証
        )

        # データ取得例（Locatorでテキスト取得）
        title = scraper.get_text("h1")
        logger.info(f"Page title: {title}")

        # ダウンロード例
        # zip_path = scraper.download_file(
        #     link_name="データダウンロード",
        #     expected_filename_pattern="*.zip"
        # )
        # logger.info(f"Downloaded file: {zip_path}")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()

    logger.info("Script completed successfully")
