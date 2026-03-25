---
name: notion-pdf
description: NotionページをPDFファイルに変換するスキル。Notion MCPでページ内容を取得し、見栄えのよいPDFとして出力する。ユーザーがNotionページのURL・ID・タイトルを指定してPDF化・PDF変換・PDF出力・印刷用出力を依頼した場合に使用する。「このNotionページをPDFにして」「NotionページをPDFに変換して」「Notionを保存したい」「このページを印刷したい」「ドキュメントをPDFで共有したい」といった表現で起動する。ユーザーの発言にNotionページのURLが含まれていてPDF化の意図がある場合は、明示的にPDFと言っていなくても積極的にこのスキルの使用を検討する。
license: MIT (see LICENSE.txt)
---

# Notion → PDF 変換スキル

NotionページをNotion MCPで取得し、スタイリングされたPDFに変換する。

## 前提条件

- Notion MCP が接続されていること（`mcp_notion_API-*` ツールが使用可能）
- Node.js がインストールされていること
- Chrome/Chromium が環境にあること（自動検出される）

## ワークフロー

### ステップ1: 対象ページの特定

ユーザーからNotionページの情報を受け取る。

- **URLが提供された場合**: URLからページIDを抽出する
  - 形式: `https://www.notion.so/.../<title>-<page-id>` または `https://www.notion.so/<page-id>`
  - URLの末尾32文字（ハイフンなし16進数）がページID
  - ハイフン付きUUID形式（`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）はそのまま使用可能
- **IDが提供された場合**: そのまま使用
- **タイトルが提供された場合**: `mcp_notion_API-post-search` で検索し、候補をユーザーに提示して選んでもらう
- **曖昧な場合**: どのページか確認する

### ステップ2: ページ内容の取得（インクリメンタル処理）

コンテキスト制限に対応するため、ブロック取得とHTML変換を**バッチ単位で交互に**行う。全ブロックのJSONをメモリに保持しない。

1. `mcp_notion_API-retrieve-a-page` でページメタデータ（タイトル、プロパティ）を取得
2. HTMLファイルを作成し、テンプレートの `<head>` 〜 `<article class="markdown-body">` + `<h1>タイトル</h1>` を書き込む
3. `mcp_notion_API-get-block-children` で子ブロックを1ページ分取得
4. 取得したブロックを即座にHTMLに変換し、ファイルに追記する
5. `has_children: true` のブロックは子ブロックを取得して変換（再帰の深さ上限: 5階層）
6. レスポンスに `has_more: true` がある場合は `start_cursor` で次ページを取得し、手順4〜5を繰り返す
7. 全ブロック処理後、`</article>` + スクリプトタグ + `</body></html>` を書き込んで閉じる

**リストのグルーピング**: 連続するリストアイテムの `<ul>` / `<ol>` ラッパーの開閉は、前回バッチの末尾ブロックタイプを記憶して管理する。

子ページを含める場合は、`child_page` タイプのブロックIDで再帰的にステップ2を実行する。

### ステップ3: HTML生成

取得したブロックデータをもとにHTMLを生成する。

- HTMLテンプレートは `references/html-template.md` を参照
- ブロック → HTML変換ルールは `references/block-to-html.md` を参照

**重要なポイント**:

- `data-color-mode="light"` 属性が必須（Primer CSSのテーマ変数を有効化）
- mermaid コードブロックがある場合のみ mermaid `<script>` タグを挿入（CDN非対応環境でのタイムアウト防止）
- 数式（`equation` ブロック / `rich_text` 内の `type: "equation"`）がある場合のみ KaTeX の CSS + `<script>` タグを挿入
- 画像は `<img src="url">` としてそのまま含める（PDF変換スクリプトがダウンロード・Base64埋め込みを処理する）
- トグルは `<details open>` で常に展開状態にする（PDFでは折りたたみ不可）
- テーブルは `<table>` + `<thead>` / `<tbody>` で構成

生成したHTMLを作業ディレクトリに保存する。ファイル名: `{ページタイトル}.html`

### ステップ4: PDF変換

スキルディレクトリの `scripts/html-to-pdf.mjs` を使用してPDFに変換する。puppeteer-core で HTML を開き、CSS読み込みと mermaid 図・KaTeX 数式のレンダリングを待ってからPDF化するスクリプト。

Chrome/Chromium バイナリは環境から自動検出される（`CHROME_PATH` 環境変数でも指定可能）。HTML内の CDN URL は、`scripts/vendor/` にローカルファイルがあれば自動的にローカルパスに置換される（Primer CSS は `vendor/primer.css` に同梱済み）。

スキルディレクトリのパスは、このファイル（SKILL.md）が存在するディレクトリ。

```bash
# 依存パッケージのインストール（node_modules が存在しない場合のみ）
npm install --prefix <skill-dir>/scripts

# PDF生成
node <skill-dir>/scripts/html-to-pdf.mjs <input.html> <output.pdf> [--format=A4]
```

オプション:
- `--format=A4`（デフォルト）/ `--format=Letter` 等
- `--margin=20mm`（デフォルト）

### ステップ5: 完了

1. 生成されたPDFのパスをユーザーに報告
2. 一時HTMLファイルを削除
3. 追加ページの変換が必要か確認

## オプション

ユーザーが指定可能。指定がなければデフォルトを使用し、事前に聞かない。

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| 出力ファイル名 | ページタイトル.pdf | PDFのファイル名 |
| 用紙サイズ | A4 | A4, Letter 等 |
| 子ページ含む | false | サブページも含めるか |

## エラーハンドリング

- **Notion MCPが未接続**: `mcp_notion_API-*` ツールが使えない場合、MCP接続設定を確認するよう案内する
- **ページが見つからない**: URL/ID/タイトルの再確認を促す。検索結果が複数ある場合は候補を提示
- **puppeteer-core未インストール**: `npm install --prefix <skill-dir>/scripts` の実行を提案
- **Chrome が見つからない**: `CHROME_PATH` 環境変数の設定か Chrome/Chromium のインストールを案内
- **画像取得失敗**: PDF変換スクリプトが画像ダウンロードに失敗した場合、その画像は空白になるがPDF生成は続行。ログの Warning をユーザーに報告
- **ブロック取得のページネーション**: 100ブロック超のページでは `has_more` を確認し、全ブロック取得するまで繰り返す
- **再帰の深さ超過**: ネスト5階層を超えた場合はそれ以上の子ブロック取得をスキップし、「（省略）」と表示する
