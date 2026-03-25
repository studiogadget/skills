#!/usr/bin/env node

/**
 * HTML → PDF 変換スクリプト
 * puppeteer-core を使用してHTMLファイルをPDFに変換する。
 * Chrome/Chromium バイナリは環境から自動検出する。
 * CDN URL はローカルに node_modules があれば自動的にローカルパスに置換する。
 *
 * Usage:
 *   node html-to-pdf.mjs <input.html> [output.pdf] [--format=A4] [--margin=20mm]
 */

import puppeteer from 'puppeteer-core';
import { readFileSync, writeFileSync, unlinkSync, existsSync } from 'fs';
import { resolve, dirname, join, basename } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// --- Chrome バイナリ自動検出 ---

function findChrome() {
  // 1. 環境変数
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) {
    return process.env.CHROME_PATH;
  }

  // 2. Windows 専用ロジック
  if (process.platform === 'win32') {
    // 2-1. where chrome コマンド（Windows 版 which）
    try {
      const p = execSync('where chrome 2>nul', { encoding: 'utf8' }).trim().split('\n')[0].trim();
      if (p && existsSync(p)) return p;
    } catch {}

    // 2-2. 既定インストールパス
    const chromeName = join('Google', 'Chrome', 'Application', 'chrome.exe');
    for (const base of [
      process.env.ProgramFiles,
      process.env['ProgramFiles(x86)'],
      process.env.LOCALAPPDATA,
    ]) {
      if (!base) continue;
      const p = join(base, chromeName);
      if (existsSync(p)) return p;
    }

    // 2-3. puppeteer キャッシュ（Windows 向け）
    const home = process.env.USERPROFILE || '';
    const cacheDir = join(home, '.cache', 'puppeteer', 'chrome');
    if (existsSync(cacheDir)) {
      try {
        const result = execSync(
          `dir /b /s "${join(cacheDir, 'chrome-win64', 'chrome.exe')}" 2>nul`,
          { encoding: 'utf8' },
        ).trim().split('\n')[0].trim();
        if (result && existsSync(result)) return result;
      } catch {}
    }

    return null;
  }

  // 3. Unix/macOS: よく使われるコマンド名
  for (const cmd of ['chromium-browser', 'chromium', 'google-chrome', 'google-chrome-stable']) {
    try {
      const p = execSync(`which ${cmd} 2>/dev/null`, { encoding: 'utf8' }).trim();
      if (p) return p;
    } catch {}
  }

  // 4. puppeteer キャッシュ内を検索（Unix/macOS）
  const home = process.env.HOME || process.env.USERPROFILE || '';
  const cacheDir = join(home, '.cache', 'puppeteer', 'chrome');
  if (existsSync(cacheDir)) {
    try {
      const result = execSync(
        `find "${cacheDir}" -type f \\( -name "chrome" -o -name "Google Chrome for Testing" \\) 2>/dev/null | head -1`,
        { encoding: 'utf8' },
      ).trim();
      if (result && existsSync(result)) return result;
    } catch {}
  }

  // 5. macOS 固有パス
  for (const p of [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ]) {
    if (existsSync(p)) return p;
  }

  return null;
}

// --- CDN URL をローカルパスに置換 ---

function resolveLocalAssets(html) {
  // Primer CSS: vendor/ → node_modules/ の順で検索
  const primerPaths = [
    join(__dirname, 'vendor', 'primer.css'),
    join(__dirname, 'node_modules', '@primer', 'css', 'dist', 'primer.css'),
  ];
  for (const p of primerPaths) {
    if (existsSync(p)) {
      html = html.replace(
        /https?:\/\/cdn\.jsdelivr\.net\/npm\/@primer\/css@\d+\/dist\/primer\.css/g,
        `file://${p}`,
      );
      break;
    }
  }

  // mermaid.js
  const mermaidLocal = join(__dirname, 'node_modules', 'mermaid', 'dist', 'mermaid.esm.min.mjs');
  if (existsSync(mermaidLocal)) {
    html = html.replace(
      /https?:\/\/cdn\.jsdelivr\.net\/npm\/mermaid@\d+\/dist\/mermaid\.esm\.min\.mjs/g,
      `file://${mermaidLocal}`,
    );
  }

  return html;
}

// --- 外部画像を Base64 data URI に埋め込み ---

async function embedImages(html) {
  const imgRegex = /<img\s+[^>]*src=["'](https?:\/\/[^"']+)["'][^>]*>/gi;
  const matches = [...html.matchAll(imgRegex)];
  if (matches.length === 0) return html;

  console.error(`Downloading ${matches.length} image(s)...`);

  const results = await Promise.allSettled(
    matches.map(async (match) => {
      const url = match[1];
      const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
      if (!res.ok) throw new Error(`HTTP ${res.status} for ${url.slice(0, 80)}...`);
      const buffer = Buffer.from(await res.arrayBuffer());
      const contentType = res.headers.get('content-type') || 'image/png';
      return {
        original: match[0],
        url,
        dataUri: `data:${contentType};base64,${buffer.toString('base64')}`,
      };
    }),
  );

  let result = html;
  let downloaded = 0;
  let failed = 0;

  for (const r of results) {
    if (r.status === 'fulfilled') {
      result = result.replace(
        r.value.original,
        r.value.original.replace(/src=["']https?:\/\/[^"']+["']/, `src="${r.value.dataUri}"`),
      );
      downloaded++;
    } else {
      console.error(`  Warning: ${r.reason.message}`);
      failed++;
    }
  }

  console.error(`  ${downloaded} downloaded, ${failed} failed`);
  return result;
}

// --- メイン処理 ---

const args = process.argv.slice(2);
const flags = {};
const positional = [];

for (const arg of args) {
  if (arg.startsWith('--')) {
    const [key, value] = arg.slice(2).split('=');
    flags[key] = value;
  } else {
    positional.push(arg);
  }
}

const htmlPath = positional[0];
if (!htmlPath) {
  console.error('Usage: node html-to-pdf.mjs <input.html> [output.pdf] [--format=A4] [--margin=20mm]');
  process.exit(1);
}

const resolvedHtmlPath = resolve(htmlPath);
const pdfPath = positional[1]
  ? resolve(positional[1])
  : resolvedHtmlPath.replace(/\.html$/, '.pdf');

const format = flags.format || 'A4';
const marginSize = flags.margin || '20mm';
const margin = {
  top: marginSize,
  right: marginSize,
  bottom: marginSize,
  left: marginSize,
};

async function convert() {
  const chromePath = findChrome();
  if (!chromePath) {
    console.error('Error: Chrome/Chromium が見つかりません。');
    console.error('以下のいずれかを試してください:');
    console.error('  - CHROME_PATH 環境変数で Chrome のパスを指定');
    console.error('  - chromium-browser または google-chrome をインストール');
    process.exit(1);
  }
  console.error(`Using Chrome: ${chromePath}`);

  // HTML を読み込み、CDN URL をローカルパスに置換し、外部画像を埋め込む
  const originalHtml = readFileSync(resolvedHtmlPath, 'utf8');
  const resolvedHtml = resolveLocalAssets(originalHtml);
  const embeddedHtml = await embedImages(resolvedHtml);

  let targetPath = resolvedHtmlPath;
  let tempFile = null;

  if (embeddedHtml !== originalHtml) {
    tempFile = join(dirname(resolvedHtmlPath), `.tmp-${basename(resolvedHtmlPath)}`);
    writeFileSync(tempFile, embeddedHtml, 'utf8');
    targetPath = tempFile;
    console.error('Assets resolved to local/embedded');
  }

  const fileUrl = `file://${targetPath}`;

  try {
    const browser = await puppeteer.launch({
      executablePath: chromePath,
      headless: true,
      args: ['--allow-file-access-from-files'],
    });
    const page = await browser.newPage();

    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60000 });

    // mermaid 等の非同期レンダリングを待つ
    await page.evaluate(() => new Promise((resolve) => {
      const svgs = document.querySelectorAll('.mermaid svg');
      if (svgs.length > 0) return resolve();
      const observer = new MutationObserver(() => {
        if (document.querySelectorAll('.mermaid svg').length > 0) {
          observer.disconnect();
          resolve();
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(resolve, 5000);
    }));

    await page.pdf({
      path: pdfPath,
      format,
      margin,
      printBackground: true,
    });

    await browser.close();
    console.log(`PDF saved: ${pdfPath}`);
  } finally {
    if (tempFile && existsSync(tempFile)) {
      unlinkSync(tempFile);
    }
  }
}

convert().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
