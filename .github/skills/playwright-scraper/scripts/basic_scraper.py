#!/usr/bin/env python3
"""
Basic Playwright Scraper Example

ログイン認証・ページネーション・ダウンロード機能を実装した
基本的なスクレイピング例。

使用方法:
    python basic_scraper.py --config config.yaml

依存:
    - playwright
    - python-dotenv
    - pyyaml
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Playwright インポート
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Error: playwright not installed. Run: pip install playwright")
    sys.exit(1)

# ロギング設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PlaywrightScraper:
    """Playwriteベースのスクレイパー基底クラス"""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000, download_dir: Optional[str] = None):
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
        email_selector: str,
        password_selector: str,
        login_button_selector: str,
        email: str,
        password: str,
        wait_selector: Optional[str] = None,
    ) -> bool:
        """
        ログイン処理（汎用）。

        Args:
            url: ログインページURL
            email_selector: メールアドレス入力フィールドのセレクタ
            password_selector: パスワード入力フィールドのセレクタ
            login_button_selector: ログインボタンのセレクタ
            email: ログインメールアドレス（環境変数や引数から）
            password: ログインパスワード（環境変数や引数から）
            wait_selector: ログイン完了を検証するセレクタ（省略可）

        Returns:
            ログイン成功時 True

        Raises:
            PlaywrightTimeoutError: タイムアウト
            ValueError: セレクタ見つからず
        """
        try:
            logger.info(f"Navigating to {url}")
            self.page.goto(url)
            self.page.wait_for_load_state("domcontentloaded")

            # メールアドレス入力
            logger.debug(f"Filling email field: {email_selector}")
            self.page.fill(email_selector, email)

            # パスワード入力
            logger.debug(f"Filling password field: {password_selector}")
            self.page.fill(password_selector, password)

            # ログインボタン クリック
            logger.info("Clicking login button")
            self.page.click(login_button_selector)

            # ページロード完了を待機
            self.page.wait_for_load_state("networkidle")
            logger.info("Login page loaded after click")

            # ログイン完了を検証（オプション）
            if wait_selector:
                self.page.wait_for_selector(wait_selector, timeout=self.timeout_ms)
                logger.info(f"Login verification selector found: {wait_selector}")

            logger.info("Login successful")
            return True

        except PlaywrightTimeoutError as e:
            logger.error(f"Login timeout (expected selector: {wait_selector})", exc_info=True)
            raise ValueError("ログイン処理がタイムアウト。パスワード確認、セレクタを確認してください。") from e
        except Exception:
            logger.error("Login failed", exc_info=True)
            raise

    def download_file(self, link_selector: str, expected_filename_pattern: Optional[str] = None) -> Optional[Path]:
        """
        ファイルダウンロード処理（Playwright標準パターン）。

        ダウンロードの完了を確実に待機するため、download.path() メソッドを使用します。
        このメソッドはダウンロードが完全に完了するまでブロックします。

        Args:
            link_selector: ダウンロードリンク/ボタンのセレクタ
            expected_filename_pattern: 期待するファイル名パターン（チェック用、オプション）

        Returns:
            ダウンロードディレクトリ内のファイルパス

        Raises:
            RuntimeError: ダウンロード失敗（イベント未発生またはpath()失敗）
            PlaywrightTimeoutError: セレクタ見つからずまたはタイムアウト
        """
        downloaded_file = None

        def handle_download(download):
            nonlocal downloaded_file
            downloaded_file = download
            logger.debug(f"Download event received: {download.suggested_filename}")

        try:
            # ダウンロードハンドラを登録（クリック前）
            self.page.on("download", handle_download)

            # ダウンロードリンクをクリック
            logger.info(f"Clicking download link: {link_selector}")
            self.page.click(link_selector)

            # ダウンロード開始を確認
            if not downloaded_file:
                raise RuntimeError("Download did not start (no download event). Link selector may be incorrect.")

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
            logger.error(f"Download failed: {str(e)}", exc_info=True)
            raise RuntimeError(
                f"Download completion wait failed. Expected file: {expected_filename_pattern or 'unknown'}. Error: {e}"
            ) from e
        finally:
            self.page.remove_listener("download", handle_download)

    def get_text(self, selector: str) -> str:
        """
        セレクタからテキストを取得。

        Args:
            selector: CSS/XPathセレクタ

        Returns:
            テキスト内容

        Raises:
            ValueError: セレクタ見つからず
        """
        try:
            text = self.page.text_content(selector)
            if text is None:
                raise ValueError(f"Element not found: {selector}")
            return text.strip()
        except Exception:
            logger.error(f"Failed to get text from {selector}", exc_info=True)
            raise

    def get_attribute(self, selector: str, attr: str) -> Optional[str]:
        """
        セレクタから属性値を取得。

        Args:
            selector: CSS/XPathセレクタ
            attr: 属性名

        Returns:
            属性値（存在しない場合 None）
        """
        try:
            value = self.page.get_attribute(selector, attr)
            return value
        except Exception:
            logger.warning(f"Failed to get attribute {attr} from {selector}", exc_info=True)
            return None


# 使用例
if __name__ == "__main__":
    # 環境変数読み込み
    load_dotenv()

    # 設定
    EMAIL = os.environ.get("EMAIL", "your_email@example.com")
    PASSWORD = os.environ.get("PASSWORD", "your_password")

    scraper = None
    try:
        # スクレイパー初期化
        scraper = PlaywrightScraper(headless=True, download_dir="./downloads")
        scraper.launch()

        # ログイン
        scraper.login(
            url="https://sec-sso.click-sec.com/loginweb/",
            email_selector="#loginId",
            password_selector="#password",
            login_button_selector="button[type='submit']",
            email=EMAIL,
            password=PASSWORD,
            wait_selector=".welcome-message",  # ログイン完了を検証
        )

        # データ取得例（ページソースから確認したセレクタを使用）
        title = scraper.get_text("title")
        logger.info(f"Page title: {title}")

        # ダウンロード例
        # zip_path = scraper.download_file(
        #     link_selector="a[href*='download']",
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
