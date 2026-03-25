# Notion APIブロック → HTML 変換ルール

Notion API（`mcp_notion_API-get-block-children`）が返すブロックをHTMLに変換するためのルール。

## リッチテキスト（rich_text）の変換

各ブロックの `rich_text` 配列を処理する。各要素の `annotations` でスタイルを適用する。

| annotations プロパティ | HTML |
|----------------------|------|
| `bold: true` | `<strong>text</strong>` |
| `italic: true` | `<em>text</em>` |
| `strikethrough: true` | `<del>text</del>` |
| `underline: true` | `<u>text</u>` |
| `code: true` | `<code>text</code>` |
| `color: "red"` | `<span style="color: #cf222e">text</span>` |
| `color: "red_background"` | `<span style="background-color: #ffebe9">text</span>` |

リンク: `rich_text[].href` が存在する場合 → `<a href="url">text</a>`

複数の annotations は組み合わせ可能（例: bold + italic → `<strong><em>text</em></strong>`）。

### 色マッピング

| Notion color | テキスト色 | 背景色（`_background`） |
|-------------|-----------|----------------------|
| gray | #6e7781 | #f6f8fa |
| brown | #7c4b24 | #f5e0dc |
| orange | #d4761c | #fff1e5 |
| yellow | #bf8700 | #fff8c5 |
| green | #1a7f37 | #dafbe1 |
| blue | #0969da | #ddf4ff |
| purple | #8250df | #fbefff |
| pink | #bf3989 | #ffeff7 |
| red | #cf222e | #ffebe9 |

## ブロックタイプ別の変換

### テキスト系

| ブロックタイプ | HTML |
|-------------|------|
| `paragraph` | `<p>{rich_text}</p>` |
| `heading_1` | `<h1>{rich_text}</h1>` |
| `heading_2` | `<h2>{rich_text}</h2>` |
| `heading_3` | `<h3>{rich_text}</h3>` |
| `quote` | `<blockquote>{rich_text}</blockquote>` |
| `divider` | `<hr>` |

### リスト系

| ブロックタイプ | HTML |
|-------------|------|
| `bulleted_list_item` | `<li>{rich_text}</li>` を `<ul>` で囲む |
| `numbered_list_item` | `<li>{rich_text}</li>` を `<ol>` で囲む |
| `to_do` | `<li>` + チェックボックス（`checked: true` → ☑、`false` → ☐） |

連続する同種のリストアイテムは1つの `<ul>` / `<ol>` にまとめる。異なるタイプが来たらリストを閉じる。

ネストされたリスト（`has_children: true`）は子ブロックを取得し、`<li>` 内にネストした `<ul>` / `<ol>` を配置する。

### コードブロック

```html
<!-- 通常のコードブロック -->
<pre><code class="language-{language}">{rich_text（プレーンテキスト）}</code></pre>

<!-- mermaid コードブロック（language が "mermaid" の場合）-->
<pre class="mermaid">{rich_text（プレーンテキスト）}</pre>
```

**mermaid の場合は `<code>` タグを付けない。** mermaid.js が `<pre class="mermaid">` を検出して図に変換する。

### テーブル

`table` ブロックの子ブロック（`table_row`）を取得して構成する。

```html
<table>
  <thead>
    <tr>
      <th>{cells[0] の rich_text}</th>
      <th>{cells[1] の rich_text}</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>{cells[0] の rich_text}</td>
      <td>{cells[1] の rich_text}</td>
    </tr>
  </tbody>
</table>
```

- `table.has_column_header: true` → 最初の行を `<thead>` にする
- `table.has_row_header: true` → 各行の最初のセルを `<th>` にする

### トグル（折りたたみ）

```html
<details open>
  <summary>{rich_text}</summary>
  <!-- 子ブロックをHTML変換して配置 -->
</details>
```

`open` 属性を必ず付ける（PDFでは折りたたみが機能しない）。

`heading_1` / `heading_2` / `heading_3` に `is_toggleable: true` がある場合もトグルとして扱う:

```html
<details open>
  <summary><h2 style="display:inline">{rich_text}</h2></summary>
  <!-- 子ブロックをHTML変換して配置 -->
</details>
```

### Callout

```html
<div class="callout">
  <p>{icon（emoji等）} {rich_text}</p>
  <!-- 子ブロックがあれば追加 -->
</div>
```

`color` フィールドに応じてクラスを付与:
- `blue` / `blue_background` → `.callout`（デフォルト青）
- `yellow` / `yellow_background` → `.callout .callout-warning`
- `red` / `red_background` → `.callout .callout-error`
- `green` / `green_background` → `.callout .callout-success`

### 画像

```html
<img src="{image.file.url または image.external.url}" alt="{caption の rich_text}">
```

画像URLはそのまま `src` に設定する。S3署名付きURLであっても省略しない。PDF変換スクリプトが自動的にダウンロードしてBase64に変換する。

caption がある場合は `<figure>` + `<figcaption>` で囲む:

```html
<figure>
  <img src="{url}" alt="{caption}">
  <figcaption>{caption の rich_text}</figcaption>
</figure>
```

### 数式

#### ブロック数式（`equation` ブロックタイプ）

```html
<div class="math-display">{expression}</div>
```

#### インライン数式（`rich_text` 内の `type: "equation"`）

`rich_text` 配列の要素に `type: "equation"` がある場合:

```html
<span class="math-inline">{equation.expression}</span>
```

KaTeX がページロード時に `.math-inline` / `.math-display` を検出してレンダリングする。テンプレートのKaTeXスクリプトは `references/html-template.md` を参照。

### その他のブロック

| ブロックタイプ | HTML変換 |
|-------------|---------|
| `bookmark` | `<a href="{url}">{caption または url}</a>` |
| `embed` | `<a href="{url}">{caption または "埋め込みコンテンツ"}</a>` |
| `file` | `<a href="{url}">{caption または filename}</a>` |
| `pdf` | `<a href="{url}">{caption または "PDF"}</a>` |
| `equation` | `<div class="math-display">{expression}</div>`（KaTeXでレンダリング） |
| `column_list` | `<div style="display:flex; gap:16px">` で子カラムを横並び |
| `column` | `<div style="flex:1">` で子ブロックを配置 |
| `child_page` | `<h3>{title}</h3>`（子ページ含むオプションがONなら再帰取得） |
| `child_database` | `<h3>{title}</h3>`（データベースの表示は非対応、タイトルのみ） |
| `synced_block` | 子ブロックをそのまま展開して変換 |
| `breadcrumb` | 無視 |
| `table_of_contents` | 無視 |

## 処理の順序

1. `mcp_notion_API-retrieve-a-page` でタイトルを取得し `<h1>` として使用
2. `mcp_notion_API-get-block-children` で全ブロック取得（ページネーション対応）
3. `has_children: true` のブロックは再帰的に子ブロックを取得
4. ブロックを先頭から順にHTMLに変換（連続リストアイテムのグルーピングに注意）
5. HTMLテンプレート（`references/html-template.md`）に本文を挿入
6. 数式が存在する場合のみ KaTeX の CSS + JS を挿入
7. mermaid ブロックが存在する場合のみ mermaid スクリプトを挿入
