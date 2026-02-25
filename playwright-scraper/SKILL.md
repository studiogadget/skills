````skill
---
name: playwright-scraper
description: ログイン認証・ページネーション・ダウンロード機能を伴うWebスクレイピング実装に使用。「Playwrightでサイト○○からデータを取得したい」「ログインしてZIPをダウンロードしたい」という依頼で起動。ロケーター判定 → スクレイピングロジック実装 → ダウンロード・待機処理の統合で進める。
---

# Playwright Scraper

## 概要

Playwrightを使った**動的Webスクレイピング**実装ガイド。
ログイン認証・ページネーション・ZIPダウンロードなど複数ステップの自動化を、**Locator中心**で実装する。

Locatorは要素操作時に自動待機・自動リトライを行うため、`query_selector` / `wait_for_selector` による手動待機より堅牢。

## 作業手順

### Step 1: ロケーター判定

ユーザーが提供したページソース（HTML）から適切なロケーターを決定する。

- ページソースをファイルで受け取り（または URL を直接検査）
- **優先順位**: セマンティックロケーター > CSSセレクタ > XPath
  1. `page.get_by_role()` – ロール + アクセシブル名（最優先）
  2. `page.get_by_label()` – フォームラベル
  3. `page.get_by_placeholder()` – プレースホルダー
  4. `page.get_by_text()` – 表示テキスト
  5. `page.locator("css=...")` – CSS（HTMLが変わりやすい場合の最終手段）
- JSON形式でロケーターマップを出力（ユーザーが確認/修正可能）

**使用ツール**: `scripts/selector_detector.py` で自動判定

```python
# 出力例: selectors.json
{
  "login_form": {
    "email_input": "get_by_label('メールアドレス')",
    "password_input": "get_by_label('パスワード')",
    "login_button": "get_by_role('button', name='ログイン')"
  },
  "download_link": "get_by_role('link', name='ダウンロード')"
}
```

### Step 2: スクレイピングロジック実装

認証・ページネーション・ダウンロード処理を組み立て。

**ログイン処理**:
- ブラウザを起動（Chromium推奨）
- Locator経由でフォーム入力 → ログインボタンクリック（Locatorが自動待機）
- ページロード完了を待機（`page.wait_for_load_state()` 利用）

```python
# ✅ Locatorベースのログイン例
page.get_by_label("メールアドレス").fill(email)
page.get_by_label("パスワード").fill(password)
page.get_by_role("button", name="ログイン").click()
page.wait_for_load_state("networkidle")
```

**ページネーション**:
- `page.locator()` で次ページリンクを Locator として取得
- `locator.is_visible()` / `locator.count()` で存在確認
- クリックは Locator 経由（自動待機込み）

```python
# ✅ Locatorベースのページネーション例
next_btn = page.get_by_role("link", name="次へ")
while next_btn.is_visible():
    next_btn.click()
    page.wait_for_load_state("networkidle")
```

**ダウンロード**:
- `page.expect_download()` コンテキストマネージャーを使用（イベント購読管理が明確）
- Locator 経由でリンク・ボタンをクリック（withブロック内）
- ダウンロード完了を確実に待機（`download.path()` がブロック）

```python
# ✅ expect_download()コンテキストマネージャーを使用（推奨）
with page.expect_download() as download_info:
    page.get_by_role("link", name="ダウンロード").click()  # Locator使用
download = download_info.value
file_path = Path(download.path())  # ダウンロード完了まで自動ブロック
```

### Step 3: エラーハンドリング・ロギング統合

タイムアウト / Locator見つからず / ダウンロード失敗 時の対応。

- 具体的な例外で捕捉（`playwright.sync_api.TimeoutError` など）
- 構造化ログで追跡（`logger.debug()` / `logger.error()` with exc_info）
- リトライ機構は必要に応じて（最大3回程度）
- Locatorは自動リトライするため、固定待機 (`time.sleep`) は不要

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
- Locator見つからず時は詳細メッセージ（HTML スナップショット相対パス等）

## 使用する同梱リソース

- [`scripts/selector_detector.py`](scripts/selector_detector.py): ページソースからロケーター候補を自動抽出
- [`scripts/basic_scraper.py`](scripts/basic_scraper.py): ログイン・ページネーション・ダウンロードの実装例
- [`references/docs_links.md`](references/docs_links.md): 公式ドキュメント・API リファレンス
- [`references/best_practices.md`](references/best_practices.md): ログイン待機・タイムアウト・リトライの実装パターン

## ダウンロード完了待機のパターン比較

Playwrightでファイルダウンロードを実装する際、完了待機の方法は3つのパターンがあります：

### パターンA: `page.expect_download()` コンテキストマネージャー（推奨 ⭐）

```python
# ✅ イベント購読の寿命管理が明確（withブロック内で完結）
with page.expect_download() as download_info:
    page.get_by_role("link", name="ダウンロード").click()
download = download_info.value
file_path = Path(download.path())  # ダウンロード完了までブロック
target_path = self.download_dir / download.suggested_filename
shutil.copy2(file_path, target_path)
```

**メリット**:
- **イベント購読が明確** - withブロック内で管理
- 最新のPlaywright推奨パターン
- ダウンロード完了を確実に待機
- ファイルが確実に書き込まれたことを保証
- `basic_scraper.py` で採用

### パターンB: `page.on()` + `download.path()`（非推奨）

```python
# ❌ イベント購読の寿命管理が暗黙的
def handle_download(download):
    file_path = Path(download.path())
    target_path = self.download_dir / download.suggested_filename
    shutil.copy2(file_path, target_path)

page.on("download", handle_download)
page.get_by_role("link", name="ダウンロード").click()
```

**問題点**:
- イベントハンドラの購読終了管理が曖昧
- 複数ダウンロード時に順序や完了保証が不明確

### パターンC: `page.wait_for_load_state()` のみ（非推奨）

```python
# ❌ ダウンロード完了を明示的に待機しない
page.on("download", handle_download)
page.get_by_role("link", name="ダウンロード").click()
page.wait_for_load_state("networkidle")  # リスク: race condition
```

**問題点**:
- ダウンロード完了を保証しない（ネットワークイベント終了と異なる）
- ファイルが部分的に書き込まれる可能性

**推奨**: **パターンA** (`page.expect_download()` コンテキストマネージャー）を使用してください。

## Locator 優先の理由

| 比較項目 | `query_selector` | Locator |
|---|---|---|
| 要素待機 | 手動（`wait_for_selector` 必要） | 自動（操作時に自動待機） |
| Stale Element | 再取得が必要 | 自動リトライで回避 |
| 複数セレクタ試行 | ループで個別実装 | `locator.or_()` で宣言的に記述 |
| アクセシビリティ | CSSのみ | ロール/ラベルで意味ベース検索可 |
| 公式推奨 | 非推奨（旧API） | 推奨（Current API） |

## 参考URL

- **Locators（主要）**: https://playwright.dev/python/docs/locators
- **Page API**: https://playwright.dev/python/docs/api/class-page
- **Locator API**: https://playwright.dev/python/docs/api/class-locator
- **Error クラス**: https://playwright.dev/python/docs/api/class-error
- **Best Practices**: https://playwright.dev/python/docs/best-practices

## チェックリスト

実装完了時に以下を確認:

- [ ] `query_selector` / `wait_for_selector` を使わず Locator を使用している
- [ ] セマンティックロケーター（`get_by_role`, `get_by_label` 等）を優先している
- [ ] ログイン後のページロード完了を明示的に待機している
- [ ] ダウンロード時に `page.expect_download()` コンテキストマネージャーでダウンロードを待機している
- [ ] 認証情報を環境変数で管理している（ハードコード禁止）
- [ ] タイムアウト時に具体的なエラーメッセージを出力している
- [ ] 構造化ログ（JSON or 標準format）で実行過程を記録している
- [ ] `make check-all` で Python syntax / lint / typecheck に合格している

```
````
