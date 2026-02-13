---
name: playwright-scraper
description: ログイン認証・ページネーション・ダウンロード機能を伴うWebスクレイピング実装に使用。「Playwrightでサイト○○からデータを取得したい」「ログインしてZIPをダウンロードしたい」という依頼で起動。セレクタ自動判定 → スクレイピングロジック実装 → ダウンロード・待機処理の統合で進める。
---

# Playwright Scraper

## 概要

Playwrightを使った**動的Webスクレイピング**実装ガイド。
静的サイト対応で、ログイン認証・ページネーション・ZIPダウンロードなど、複数ステップの自動化を実装。

## 作業手順

### Step 1: セレクタ自動判定

ユーザーが提供したページソース（HTML）から必要なセレクタを自動判定。

- ページソースをファイルで受け取り（または URL を直接検査）
- セレクタ候補を抽出（ID / Class / XPath）
- JSON形式でセレクタマップを出力（ユーザーが確認/修正可能）

**使用ツール**: `scripts/selector_detector.py` で自動判定

```python
# 出力例: selectors.json
{
  "login_form": {
    "email_input": "#loginId",
    "password_input": "#password",
    "login_button": "button[type='submit']"
  },
  "download_link": "a[href*='zip']"
}
```

### Step 2: スクレイピングロジック実装

認証・ページネーション・ダウンロード処理を組み立て。

**ログイン処理**:
- ブラウザを起動（Chromium推奨）
- フォーム入力 → ログインボタン クリック
- ページロード完了を待機（`page.wait_for_load_state()` 利用）

**ページネーション**:
- セレクタで次ページリンク検出
- 存在するまでループ、ページごと処理
- タイムアウト・重複排除に注意

**ダウンロード**:
- 事前に download ハンドラ登録 (`page.on("download", handler)`)
- リンク・ボタン をクリック
- ダウンロード完了を待機

### Step 3: エラーハンドリング・ロギング統合

タイムアウト / セレクタ見つからず / ダウンロード失敗 時の対応。

- 具体的な例外で捕捉（`playwright.async_api.TimeoutError` など）
- 構造化ログで追跡（`logger.debug()` / `logger.error()` with exc_info）
- リトライ機構は必要に応じて（最大3回程度）

## 実装例

**入力**:
```yaml
target_url: "https://example.com/login"
selectors_file: "config/selectors.json"  # Step 1 の出力
credentials:
  email: "${EMAIL}"          # 環境変数参照
  password: "${PASSWORD}"
download_dir: "./downloads"
page_limit: 5                     # ページネーション上限
```

**期待する出力**:
- `${download_dir}/data_*.zip` ダウンロード成功
- `scrape_log.json` 構造化ログ（取得項目数・エラー・実行時間）
- セレクタ見つからず時は詳細メッセージ（HTML スナップショット相対パス等）

## 使用する同梱リソース

- [`scripts/selector_detector.py`](scripts/selector_detector.py): ページソースからセレクタ候補を自動抽出
- [`scripts/basic_scraper.py`](scripts/basic_scraper.py): ログイン・ページネーション・ダウンロードの実装例
- [`references/docs_links.md`](references/docs_links.md): 公式ドキュメント・API リファレンス
- [`references/best_practices.md`](references/best_practices.md): ログイン待機・タイムアウト・リトライの実装パターン

## ダウンロード完了待機のパターン比較

Playwrightでファイルダウンロードを実装する際、完了待機の方法は2つのパターンがあります：

### パターンA: `download.path()` で完了を待機（推奨）

```python
def handle_download(download):
    # download.path() はダウンロード完了までブロック
    file_path = Path(download.path())
    target_path = self.download_dir / download.suggested_filename
    shutil.copy2(file_path, target_path)
    return target_path
```

**メリット**:
- Playwright標準パターン
- ダウンロード完了を確実に待機
- ファイルが確実に書き込まれたことを保証
- ユーザーはすぐにファイルを使用可能

**デメリット**: 特になし

### パターンB: `page.wait_for_load_state("networkidle")` で待機

```python
def handle_download(download):
    # networkidle は待機するが、download完了を保証しない
    download.save_as(self.download_dir / download.suggested_filename)

page.on("download", handle_download)
page.click(link_selector)
page.wait_for_load_state("networkidle")  # リスク
```

**メリット**:
- ネットワーク活動の終了を確認

**デメリット**:
- ダウンロード完了を保証しない
- ファイル書き込み完了前に処理が進む可能性
- race conditionのリスク

**推奨**: パターンA（`download.path()`）を使用してください。basic_scraper.pyはこのパターンで実装されています。

## チェックリスト

実装完了時に以下を確認:

- [ ] セレクタ判定ロジックが HTML 解析で正しくセレクタを抽出している
- [ ] ログイン後のページロード完了を明示的に待機している
- [ ] ダウンロード時に `download.path()` で完了を確実に待機している
- [ ] 認証情報を環境変数で管理している（ハードコード禁止）
- [ ] タイムアウト時に具体的なエラーメッセージを出力している
- [ ] 構造化ログ（JSON or 標準format）で実行過程を記録している
- [ ] `make check-all` で Python syntax / lint / typecheck に合格している
