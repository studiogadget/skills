#!/usr/bin/env python3
"""
Selector Detector - HTMLからセレクタ候補を自動抽出

ページソース（HTML）から、ログインフォーム・リンク等のセレクタを自動判定。
出力は JSON 形式で、ユーザーが確認・修正可能。

使用方法:
    python selector_detector.py page.html --output selectors.json
    python selector_detector.py page.html --keywords login,password,download
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    sys.exit(1)


class SelectorDetector:
    """HTMLからセレクタを自動検出"""

    def __init__(self, html: str):
        """
        初期化。

        Args:
            html: HTMLテキスト
        """
        self.soup = BeautifulSoup(html, "html.parser")
        self.selectors: Dict[str, Any] = {}

    def detect_login_form(self) -> Optional[Dict[str, str]]:
        """
        ログインフォームのセレクタを検出。

        Returns:
            {
                "form": "form#loginForm",
                "email_input": "#email",
                "password_input": "#password",
                "submit_button": "button[type='submit']"
            }
        """
        login_form = {}

        # フォーム要素検出
        form = self._find_element_by_keywords(["form"], id_pattern=["login", "auth"])
        if form:
            login_form["form"] = self._get_css_selector(form)

        # メール入力フィールド
        email_input = self._find_element_by_keywords(
            ["input"],
            type_pattern=["email", "text"],
            id_pattern=["email", "loginId", "username"],
            name_pattern=["email", "loginId", "username"],
        )
        if email_input:
            login_form["email_input"] = self._get_css_selector(email_input)

        # パスワード入力フィールド
        password_input = self._find_element_by_keywords(
            ["input"], type_pattern=["password"], id_pattern=["password", "passwd"], name_pattern=["password", "passwd"]
        )
        if password_input:
            login_form["password_input"] = self._get_css_selector(password_input)

        # ログインボタン
        submit_button = self._find_element_by_keywords(
            ["button", "input"], type_pattern=["submit"], text_pattern=["login", "sign in", "log in"]
        )
        if submit_button:
            login_form["submit_button"] = self._get_css_selector(submit_button)

        return login_form if login_form else None

    def detect_download_links(self) -> Optional[List[Dict[str, str]]]:
        """
        ダウンロードリンクを検出。

        Returns:
            [
                {
                    "text": "Download Data",
                    "href": "/api/download/data.zip",
                    "selector": "a[href*='download']"
                },
                ...
            ]
        """
        download_links = []

        # href に "download" / "zip" / "csv" を含むリンク
        for link in self.soup.find_all("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if any(keyword in href.lower() for keyword in ["download", "zip", "csv", "export"]):
                download_links.append(
                    {
                        "text": text[:50],  # 最初の50文字
                        "href": href,
                        "selector": self._get_css_selector(link),
                    }
                )

        return download_links if download_links else None

    def detect_buttons_by_text(self, text_patterns: List[str]) -> Optional[List[Dict[str, str]]]:
        """
        テキストパターンでボタンを検出。

        Args:
            text_patterns: マッチするテキストパターン（例: ["Next", "続ける"]）

        Returns:
            [{
                "text": "Next Page",
                "selector": "button.next-btn"
            }]
        """
        buttons = []

        for button in self.soup.find_all(["button", "a"]):
            text = button.get_text(strip=True).lower()

            if any(pattern.lower() in text for pattern in text_patterns):
                buttons.append({"text": button.get_text(strip=True)[:50], "selector": self._get_css_selector(button)})

        return buttons if buttons else None

    def detect_input_fields(self) -> Optional[List[Dict[str, str]]]:
        """
        全入力フィールドを検出。

        Returns:
            [{
                "type": "email",
                "name": "email",
                "id": "user_email",
                "selector": "#user_email"
            }]
        """
        inputs = []

        for input_elem in self.soup.find_all("input"):
            input_type = input_elem.get("type", "text")
            name = input_elem.get("name", "")
            elem_id = input_elem.get("id", "")
            placeholder = input_elem.get("placeholder", "")

            inputs.append(
                {
                    "type": input_type,
                    "name": name,
                    "id": elem_id,
                    "placeholder": placeholder,
                    "selector": self._get_css_selector(input_elem),
                }
            )

        return inputs if inputs else None

    def detect_tables(self) -> Optional[List[Dict[str, Any]]]:
        """
        テーブル構造を検出（ページネーション・データ取得用）。

        Returns:
            [{
                "selector": "table#data_table",
                "rows": 10,
                "columns": ["Date", "Value", "Status"]
            }]
        """
        tables = []

        for table in self.soup.find_all("table"):
            rows = table.find_all("tr")
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])] if rows else []

            tables.append(
                {
                    "selector": self._get_css_selector(table),
                    "rows_count": len(rows),
                    "columns": headers[:10],  # 最初の10列のみ
                }
            )

        return tables if tables else None

    def _find_element_by_keywords(
        self,
        tags: List[str],
        id_pattern: Optional[List[str]] = None,
        name_pattern: Optional[List[str]] = None,
        type_pattern: Optional[List[str]] = None,
        text_pattern: Optional[List[str]] = None,
    ):
        """複数パターンで要素検出（内部用）"""
        for tag in tags:
            for elem in self.soup.find_all(tag):
                elem_id = elem.get("id", "").lower()
                elem_name = elem.get("name", "").lower()
                elem_type = elem.get("type", "").lower()
                elem_text = elem.get_text(strip=True).lower()

                # ID マッチ
                if id_pattern and any(p.lower() in elem_id for p in id_pattern):
                    return elem

                # name マッチ
                if name_pattern and any(p.lower() in elem_name for p in name_pattern):
                    return elem

                # type マッチ
                if type_pattern and any(p.lower() == elem_type for p in type_pattern):
                    return elem

                # テキストマッチ
                if text_pattern and any(p.lower() in elem_text for p in text_pattern):
                    return elem

        return None

    def _get_css_selector(self, elem) -> str:
        """
        HTML要素から CSS セレクタを生成。

        Args:
            elem: BeautifulSoup要素

        Returns:
            CSS セレクタ文字列
        """
        # ID が存在する場合は ID を使用（最も特定的）
        elem_id = elem.get("id")
        if elem_id:
            return f"#{elem_id}"

        # class が存在する場合
        classes = elem.get("class", [])
        if classes:
            return f".{'.'.join(classes[:2])}"  # 最初の2クラスまで

        # name が存在する場合
        name = elem.get("name")
        if name:
            elem_type = elem.get("type", "")
            if elem_type:
                return f"{elem.name}[name='{name}'][type='{elem_type}']"
            return f"{elem.name}[name='{name}']"

        # type 属性で特定
        elem_type = elem.get("type")
        if elem_type:
            return f"{elem.name}[type='{elem_type}']"

        # テキストで特定（最後の手段）
        text = elem.get_text(strip=True)[:30]
        if text:
            return f"{elem.name}:contains('{text}')"

        # デフォルト
        return elem.name

    def detect_all(self) -> Dict[str, Any]:
        """
        全セレクタを一括検出。

        Returns:
            {
                "login_form": {...},
                "download_links": [...],
                "input_fields": [...],
                "tables": [...],
                "next_page_buttons": [...]
            }
        """
        result = {}

        login = self.detect_login_form()
        if login:
            result["login_form"] = login

        downloads = self.detect_download_links()
        if downloads:
            result["download_links"] = downloads

        inputs = self.detect_input_fields()
        if inputs:
            result["input_fields"] = inputs

        tables = self.detect_tables()
        if tables:
            result["tables"] = tables

        next_buttons = self.detect_buttons_by_text(["next", "続く", "次", ">>"])
        if next_buttons:
            result["next_page_buttons"] = next_buttons

        return result


def main():
    """コマンドラインインターフェース"""
    parser = argparse.ArgumentParser(description="HTMLからセレクタ候補を自動抽出")
    parser.add_argument("html_file", help="HTMLファイルパス")
    parser.add_argument("--output", "-o", default="selectors.json", help="出力ファイル（デフォルト: selectors.json）")
    parser.add_argument("--keywords", help="検出対象キーワード（カンマ区切り）")

    args = parser.parse_args()

    # HTML ファイル読み込み
    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"Error: File not found: {html_path}")
        sys.exit(1)

    with html_path.open("r", encoding="utf-8") as f:
        html_content = f.read()

    # セレクタ検出
    detector = SelectorDetector(html_content)
    selectors = detector.detect_all()

    # 結果出力
    output_path = Path(args.output)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(selectors, f, ensure_ascii=False, indent=2)

    print(f"✅ Selectors detected and saved to: {output_path}")
    print(json.dumps(selectors, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
