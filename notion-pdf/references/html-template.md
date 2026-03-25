# HTMLテンプレートと変換ルール

## テンプレート

```html
<!DOCTYPE html>
<html lang="ja" data-color-mode="light" data-light-theme="light">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@primer/css@21/dist/primer.css">
<style>
  @page {
    size: A4;
    margin: 20mm;
  }
  body {
    padding: 0;
    margin: 0;
  }
  .markdown-body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "Noto Sans CJK JP", "Noto Sans JP", "Hiragino Sans",
                 Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    padding: 32px;
    max-width: none;
  }
  .markdown-body img {
    max-width: 100%;
  }
  /* --- Primer CSS 変数のフォールバック --- */
  .markdown-body table {
    border-collapse: collapse;
    width: 100%;
  }
  .markdown-body table th,
  .markdown-body table td {
    border: 1px solid #d0d7de;
    padding: 6px 13px;
  }
  .markdown-body table th {
    background-color: #f6f8fa;
    font-weight: 600;
  }
  .markdown-body table tr {
    background-color: #ffffff;
    border-top: 1px solid #d8dee4;
  }
  .markdown-body table tr:nth-child(2n) {
    background-color: #f6f8fa;
  }
  .markdown-body blockquote {
    border-left: .25em solid #d0d7de;
    color: #656d76;
  }
  .markdown-body h1,
  .markdown-body h2 {
    border-bottom: 1px solid #d8dee4;
  }
  .markdown-body h6 {
    color: #656d76;
  }
  .markdown-body hr {
    border-bottom: 1px solid #d0d7de;
  }
  .markdown-body code,
  .markdown-body tt {
    background-color: rgba(175,184,193,0.2);
  }
  .markdown-body pre {
    background-color: #f6f8fa;
  }
  .markdown-body details[open] {
    background-color: var(--bgColor-muted, #f6f8fa);
    border-radius: 6px;
    padding: 0 16px 16px;
    margin: 8px 0 16px 0;
  }
  .markdown-body details[open] > summary {
    margin: 0 -16px;
    padding: 8px 16px;
  }
  /* --- Callout / 色付き要素の補完スタイル --- */
  .callout {
    border-left: 4px solid #218bff;
    background-color: #ddf4ff;
    padding: 12px 16px;
    margin: 16px 0;
    border-radius: 0 6px 6px 0;
  }
  .callout-warning {
    border-left-color: #bf8700;
    background-color: #fff8c5;
  }
  .callout-error {
    border-left-color: #cf222e;
    background-color: #ffebe9;
  }
  .callout-success {
    border-left-color: #1a7f37;
    background-color: #dafbe1;
  }
  .section-label {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 6px;
    font-weight: 600;
    margin: 16px 0 8px 0;
  }
  .bg-gray { background-color: #f6f8fa; }
  .bg-brown { background-color: #f5e0dc; }
  .bg-orange { background-color: #fff1e5; }
  .bg-yellow { background-color: #fff8c5; }
  .bg-green { background-color: #dafbe1; }
  .bg-blue { background-color: #ddf4ff; }
  .bg-purple { background-color: #fbefff; }
  .bg-pink { background-color: #ffeff7; }
  .bg-red { background-color: #ffebe9; }
  @media print {
    .markdown-body {
      padding: 0;
    }
    .markdown-body h1,
    .markdown-body h2,
    .markdown-body h3 {
      page-break-after: avoid;
    }
    .markdown-body pre,
    .markdown-body table,
    .markdown-body img {
      page-break-inside: avoid;
    }
  }
</style>
</head>
<body>
<article class="markdown-body">
<!-- 変換したHTML本文をここに挿入 -->
</article>
<!-- 数式（equation）がある場合のみ以下を挿入 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.js"></script>
<script>
document.querySelectorAll('.math-inline').forEach(el => {
  katex.render(el.textContent, el, { throwOnError: false });
});
document.querySelectorAll('.math-display').forEach(el => {
  katex.render(el.textContent, el, { throwOnError: false, displayMode: true });
});
</script>
<!-- mermaid コードブロックがある場合のみ以下を挿入 -->
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
</script>
</body>
</html>
```

## テンプレートの重要なポイント

- **`data-color-mode="light" data-light-theme="light"`**: Primer CSSのテーマ変数を有効化する属性。これがないとテーブルのボーダー等が透明になる
- **`primer.css`（フルバンドル）**: `markdown.css` 単体ではCSS変数定義が含まれないため、フルバンドルを使う
- **KaTeX**: ページに数式（`equation` ブロックまたは `rich_text` 内の `type: "equation"`）が含まれる場合のみ、KaTeX の CSS と JS を挿入する。`.math-inline` / `.math-display` クラスの要素を検出してレンダリングする
- **mermaid.js**: `<pre class="mermaid">` を検出して図に変換する。**ページに mermaid コードブロックがない場合はスクリプトタグを省略する**（CDN非対応環境でのタイムアウト防止）
- **CDN フォールバック**: `html-to-pdf.mjs` は、ローカルの `vendor/` や `node_modules/` にファイルがあれば CDN URL を自動的にローカルパスに置換する
- **CSS変数フォールバック**: テーブルボーダー、blockquote等はテーマCSS変数に依存するため、`<style>` ブロックで明示的な色値をフォールバック定義している
- **Callout スタイル**: Primer CSSにはNotionのcallout相当のスタイルがないため、`.callout` クラスで補完している
- **用紙サイズ**: `@page { size: A4; }` をデフォルトとする。Letter等に変更する場合はこの値を変更する
- **スクリプトの挿入順**: `</article>` の後に KaTeX（数式ありの場合）→ mermaid（mermaidありの場合）→ `</body></html>` の順で挿入する
