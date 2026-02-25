# 日本語コンサルスライド デザインシステム リファレンス

PptxGenJSを使用してMcKinsey/BCG品質のコンサルティングプレゼンテーションスライドを日本語で作成するための完全な設計仕様。テックミニマリストかつ情報密度の高いエディトリアルデザインを実現する。

---

## 目次

1. [カラートークン](#カラートークン)
2. [タイポグラフィシステム](#タイポグラフィシステム)
3. [レイアウトグリッド](#レイアウトグリッド)
4. [スライドテンプレート](#スライドテンプレート)
5. [チャートスタイリング](#チャートスタイリング)
6. [テーブルスタイリング](#テーブルスタイリング)
7. [フレームワークコンポーネント](#フレームワークコンポーネント)
8. [ウォーターフォールチャート](#ウォーターフォールチャート)
9. [再利用可能コードパターン](#再利用可能コードパターン)

---

## カラートークン

全スクリプトの先頭で定数として定義する：

```javascript
// === コンサルティング カラーパレット ===
const C = {
  // 背景
  bgWhite:      "FFFFFF",
  bgLight:      "F5F7FA",   // 交互行 / パネル背景
  bgNavy:       "0B1F3F",   // タイトルスライド背景、ヘッダー行

  // テキスト
  textBlack:    "1A1A1A",
  textDark:     "333333",   // 本文、チャートラベル
  textMuted:    "888888",   // ソースライン、キャプション
  textWhite:    "FFFFFF",

  // ブランド / チャート
  royalBlue:    "1B3A6B",   // プライマリチャートカラー、タイトル下線
  blue2:        "3D6098",   // セカンダリチャート
  blue3:        "7A9CC6",   // ターシャリチャート
  blue4:        "B8CCE4",   // クォータナリチャート
  blue5:        "D9E5F2",   // 最も薄いチャート / マトリクス塗りつぶし

  // アクセント
  accentRed:    "C8102E",   // コールアウト、デルタ、アラートに控えめに使用
  accentGreen:  "2E7D32",   // ポジティブデルタ

  // 構造
  gridLine:     "D0D0D0",   // テーブルボーダー、フレームワークライン
  divider:      "1B3A6B",   // タイトル下線（細）
};
```

`C.royalBlue` のように定数名で参照し、生のHex文字列は使わない。

---

## タイポグラフィシステム

日本語プレゼンテーション用に最適化した2フォントファミリーシステム。見出し系にはセリフ体（游明朝）、本文系にはサンセリフ体（游ゴシック）を使用し、プレミアムな金融レポートの雰囲気を実現する。数字・英字にはCalibrを補助的に使用する。

| 役割 | フォント | サイズ | ウェイト | カラー | 用途 |
|------|---------|--------|---------|--------|------|
| アクションタイトル | Yu Mincho | 17-19pt | Bold | `C.bgNavy` | 全コンテンツスライドの上部 |
| セクションヘッダー | Yu Mincho | 13-15pt | Bold | `C.bgNavy` | スライド内セクションラベル |
| 本文 | Yu Gothic | 11-13pt | Regular | `C.textDark` | 説明、注釈 |
| チャートラベル | Calibri | 10pt | Regular | `C.textDark` | 軸ラベル、データラベル |
| データ数値 | Calibri | 10-11pt | Bold | `C.textBlack` | テーブル/コールアウト内の値 |
| ソースライン | Yu Gothic | 8pt | Regular | `C.textMuted` | データスライド下部 |
| ページ番号 | Calibri | 8pt | Regular | `C.textMuted` | 右下 |
| コールアウト数値 | Georgia | 36-48pt | Bold | `C.royalBlue` | 大きな統計コールアウト |
| コールアウトラベル | Yu Gothic | 10pt | Regular | `C.textDark` | 大きな統計数値の下 |

### ヘルパー関数

```javascript
// テキストオプションのファクトリ関数（常に新しいオブジェクトを生成）
const font = {
  actionTitle: () => ({
    fontFace: "Yu Mincho", fontSize: 18, bold: true, color: C.bgNavy, margin: 0
  }),
  sectionHeader: () => ({
    fontFace: "Yu Mincho", fontSize: 14, bold: true, color: C.bgNavy, margin: 0
  }),
  body: () => ({
    fontFace: "Yu Gothic", fontSize: 12, color: C.textDark, margin: 0
  }),
  dataLabel: () => ({
    fontFace: "Calibri", fontSize: 10, color: C.textDark
  }),
  source: () => ({
    fontFace: "Yu Gothic", fontSize: 8, color: C.textMuted, margin: 0
  }),
  pageNum: () => ({
    fontFace: "Calibri", fontSize: 8, color: C.textMuted, margin: 0
  }),
  calloutNum: () => ({
    fontFace: "Georgia", fontSize: 42, bold: true, color: C.royalBlue, margin: 0
  }),
  calloutLabel: () => ({
    fontFace: "Yu Gothic", fontSize: 10, color: C.textDark, margin: 0
  }),
};
```

### フォントフォールバック戦略

LibreOffice環境では游明朝/游ゴシックが利用できない場合がある。その場合のフォールバック：
- 游明朝 → "MS PMincho" → "Georgia"（最終フォールバック）
- 游ゴシック → "Meiryo UI" → "Calibri"（最終フォールバック）

PDF変換時に文字化けが発生した場合は、フォールバックフォントに切り替えて再生成すること。

---

## レイアウトグリッド

スライドサイズ: 10" × 5.625"（LAYOUT_16x9）

```
┌─────────────────────────────────────────────┐
│  0.5" マージン                               │
│  ┌─────────────────────────────────────────┐│
│  │ アクションタイトル (Yu Mincho 18pt bold) ││
│  │ ─────────────────────────── (0.5pt線)   ││  y=0.5, h=0.5
│  │                                         ││  線 at y=1.05
│  │  コンテンツエリア                        ││
│  │  (y=1.2 to y=4.8)                      ││
│  │                                         ││
│  │  利用可能: 9.0" 幅 × 3.6" 高           ││
│  │                                         ││
│  │                                         ││
│  ├─────────────────────────────────────────┤│
│  │ 出所: ...          ページ N             ││  y=5.15
│  └─────────────────────────────────────────┘│
│  0.5" マージン                               │
└─────────────────────────────────────────────┘
```

### 座標定数

```javascript
const L = {
  // マージン
  mx: 0.5,              // 左右マージン
  my: 0.5,              // 上マージン

  // コンテンツエリア
  contentX: 0.5,
  contentY: 1.2,         // タイトル + ディバイダー下
  contentW: 9.0,         // 10 - 2*0.5
  contentH: 3.6,         // コンテンツ用の利用可能高さ

  // タイトル
  titleX: 0.5,
  titleY: 0.42,
  titleW: 9.0,
  titleH: 0.55,          // 日本語テキスト用に少し高め
  dividerY: 1.02,        // タイトル下の細い線

  // フッター
  sourceX: 0.5,
  sourceY: 5.15,
  pageNumX: 9.0,
  pageNumY: 5.15,

  // カラムヘルパー
  col2W: 4.3,            // 2カラムレイアウトの各カラム幅（0.4"ギャップ含む）
  col2Gap: 0.4,
  col2RightX: 5.2,       // 0.5 + 4.3 + 0.4

  col3W: 2.73,           // 3カラムレイアウトの各カラム幅（0.4"ギャップ含む）
  col3Gap: 0.4,
  col3MidX: 3.63,
  col3RightX: 6.76,
};
```

---

## スライドテンプレート

### テンプレート: タイトルスライド（ダーク）

```javascript
function addTitleSlide(pres, { title, subtitle, date }) {
  const slide = pres.addSlide();
  slide.background = { color: C.bgNavy };

  // タイトルテキスト
  slide.addText(title, {
    x: 0.8, y: 1.4, w: 8.4, h: 1.3,
    fontFace: "Yu Mincho", fontSize: 30, bold: true,
    color: C.textWhite, align: "left", valign: "middle", margin: 0
  });

  // 細いアクセントライン
  slide.addShape(pres.shapes.LINE, {
    x: 0.8, y: 2.85, w: 2.0, h: 0,
    line: { color: C.textWhite, width: 1.0 }
  });

  // サブタイトル
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.8, y: 3.1, w: 8.4, h: 0.7,
      fontFace: "Yu Gothic", fontSize: 14, color: C.blue3,
      align: "left", valign: "top", margin: 0
    });
  }

  // 日付
  if (date) {
    slide.addText(date, {
      x: 0.8, y: 4.6, w: 8.4, h: 0.3,
      fontFace: "Calibri", fontSize: 10, color: C.blue4,
      align: "left", margin: 0
    });
  }

  return slide;
}
```

### テンプレート: 標準コンテンツスライド

```javascript
function addContentSlide(pres, { actionTitle, sourceText, pageNum }) {
  const slide = pres.addSlide();
  slide.background = { color: C.bgWhite };

  // アクションタイトル
  slide.addText(actionTitle, {
    x: L.titleX, y: L.titleY, w: L.titleW, h: L.titleH,
    ...font.actionTitle(), align: "left", valign: "top"
  });

  // タイトルディバイダーライン
  slide.addShape(pres.shapes.LINE, {
    x: L.mx, y: L.dividerY, w: L.contentW, h: 0,
    line: { color: C.divider, width: 0.5 }
  });

  // ソースライン
  if (sourceText) {
    slide.addText(`出所: ${sourceText}`, {
      x: L.sourceX, y: L.sourceY, w: 6, h: 0.3,
      ...font.source(), align: "left"
    });
  }

  // ページ番号
  if (pageNum) {
    slide.addText(String(pageNum), {
      x: L.pageNumX, y: L.pageNumY, w: 0.5, h: 0.3,
      ...font.pageNum(), align: "right"
    });
  }

  return slide;
}
```

### テンプレート: エグゼクティブサマリースライド

3〜4つの重要発見事項を構造化レイアウトでコールアウト番号付きで表示する。

```javascript
function addExecSummarySlide(pres, { actionTitle, findings, sourceText, pageNum }) {
  const slide = addContentSlide(pres, { actionTitle, sourceText, pageNum });

  findings.forEach((finding, i) => {
    const yBase = L.contentY + i * 0.85;

    // 発見番号（ロイヤルブルー円形）
    slide.addText(String(i + 1), {
      x: L.contentX, y: yBase, w: 0.35, h: 0.35,
      fontFace: "Georgia", fontSize: 14, bold: true,
      color: C.textWhite, align: "center", valign: "middle",
      fill: { color: C.royalBlue },
      margin: 0
    });

    // 発見タイトル（ボールド）
    slide.addText(finding.title, {
      x: L.contentX + 0.55, y: yBase, w: 3.5, h: 0.35,
      fontFace: "Yu Gothic", fontSize: 12, bold: true,
      color: C.textBlack, align: "left", valign: "middle", margin: 0
    });

    // 発見詳細
    slide.addText(finding.description, {
      x: L.contentX + 0.55, y: yBase + 0.35, w: 8.0, h: 0.4,
      fontFace: "Yu Gothic", fontSize: 10, color: C.textDark,
      align: "left", valign: "top", margin: 0
    });
  });

  return slide;
}
```

### テンプレート: KPIコールアウト付きサマリー

エグゼクティブサマリースライドで3〜4つの主要指標を目立つように表示する。

```javascript
function addKPIRow(slide, pres, kpis, { y }) {
  // kpis = [{ value: "34%", label: "前年比成長率", delta: "+12pp" }, ...]
  const count = kpis.length;
  const kpiW = L.contentW / count;

  kpis.forEach((kpi, i) => {
    const kpiX = L.contentX + i * kpiW;

    // 大きな数値
    slide.addText(kpi.value, {
      x: kpiX, y: y, w: kpiW, h: 0.65,
      ...font.calloutNum(), align: "center", valign: "bottom"
    });

    // ラベル
    slide.addText(kpi.label, {
      x: kpiX, y: y + 0.68, w: kpiW, h: 0.25,
      ...font.calloutLabel(), align: "center", valign: "top"
    });

    // デルタ（任意、赤または緑）
    if (kpi.delta) {
      const isPositive = kpi.delta.startsWith("+");
      slide.addText(kpi.delta, {
        x: kpiX, y: y + 0.95, w: kpiW, h: 0.2,
        fontFace: "Calibri", fontSize: 9, bold: true,
        color: isPositive ? C.accentGreen : C.accentRed,
        align: "center", margin: 0
      });
    }

    // 垂直セパレーター（最後以外）
    if (i < count - 1) {
      slide.addShape(pres.shapes.LINE, {
        x: kpiX + kpiW, y: y + 0.1, w: 0, h: 0.95,
        line: { color: C.gridLine, width: 0.5 }
      });
    }
  });
}
```

---

## チャートスタイリング

### 棒グラフ（カラムチャート）

```javascript
function addConsultingBarChart(slide, pres, { chartData, x, y, w, h, showValue }) {
  slide.addChart(pres.charts.BAR, chartData, {
    x: x || L.contentX, y: y || L.contentY,
    w: w || L.contentW, h: h || 3.2,
    barDir: "col",
    chartColors: [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5],
    chartArea: { fill: { color: C.bgWhite } },
    catAxisLabelColor: C.textDark,
    catAxisLabelFontFace: "Calibri",
    catAxisLabelFontSize: 9,
    valAxisLabelColor: C.textMuted,
    valAxisLabelFontFace: "Calibri",
    valAxisLabelFontSize: 9,
    valGridLine: { color: C.gridLine, size: 0.5 },
    catGridLine: { style: "none" },
    showValue: showValue || false,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.textBlack,
    dataLabelFontFace: "Calibri",
    dataLabelFontSize: 9,
    showLegend: chartData.length > 1,
    legendPos: "b",
    legendFontFace: "Calibri",
    legendFontSize: 9,
  });
}
```

### 積み上げ棒グラフ

```javascript
function addConsultingStackedBar(slide, pres, { chartData, x, y, w, h }) {
  slide.addChart(pres.charts.BAR, chartData, {
    x: x || L.contentX, y: y || L.contentY,
    w: w || L.contentW, h: h || 3.2,
    barDir: "col",
    barGrouping: "stacked",
    chartColors: [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5],
    chartArea: { fill: { color: C.bgWhite } },
    catAxisLabelColor: C.textDark,
    catAxisLabelFontFace: "Calibri",
    catAxisLabelFontSize: 9,
    valAxisLabelColor: C.textMuted,
    valAxisLabelFontFace: "Calibri",
    valAxisLabelFontSize: 9,
    valGridLine: { color: C.gridLine, size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: true,
    legendPos: "b",
    legendFontFace: "Calibri",
    legendFontSize: 9,
  });
}
```

### 折れ線グラフ

```javascript
function addConsultingLineChart(slide, pres, { chartData, x, y, w, h }) {
  slide.addChart(pres.charts.LINE, chartData, {
    x: x || L.contentX, y: y || L.contentY,
    w: w || L.contentW, h: h || 3.2,
    lineSize: 2,
    lineSmooth: false,   // コンサルスタイル = 角ばった線、スムーズ不可
    chartColors: [C.royalBlue, C.accentRed, C.blue3],
    chartArea: { fill: { color: C.bgWhite } },
    catAxisLabelColor: C.textDark,
    catAxisLabelFontFace: "Calibri",
    catAxisLabelFontSize: 9,
    valAxisLabelColor: C.textMuted,
    valAxisLabelFontFace: "Calibri",
    valAxisLabelFontSize: 9,
    valGridLine: { color: C.gridLine, size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: chartData.length > 1,
    legendPos: "b",
    legendFontFace: "Calibri",
    legendFontSize: 9,
    showMarker: true,
    markerSize: 5,
  });
}
```

---

## テーブルスタイリング

### コンサルティンググレード データテーブル

```javascript
function buildConsultingTable(headers, rows) {
  // ヘッダー行スタイリング
  const headerCells = headers.map(h => ({
    text: h,
    options: {
      fill: { color: C.bgNavy },
      color: C.textWhite,
      fontFace: "Yu Gothic",
      fontSize: 10,
      bold: true,
      align: "left",
      valign: "middle",
      border: { pt: 0.5, color: C.gridLine },
      margin: [4, 6, 4, 6],
    }
  }));

  // データ行（交互背景色）
  const dataRows = rows.map((row, rowIdx) => {
    return row.map((cell, colIdx) => ({
      text: String(cell),
      options: {
        fill: { color: rowIdx % 2 === 0 ? C.bgWhite : C.bgLight },
        color: C.textDark,
        fontFace: colIdx === 0 ? "Yu Gothic" : "Calibri",  // 最初の列は日本語フォント
        fontSize: 10,
        align: colIdx === 0 ? "left" : "right",  // 数値列は右寄せ
        valign: "middle",
        border: { pt: 0.5, color: C.gridLine },
        margin: [3, 6, 3, 6],
      }
    }));
  });

  return [headerCells, ...dataRows];
}

// 使用例:
// const tableData = buildConsultingTable(
//   ["指標", "2023年度", "2024年度", "変化"],
//   [["売上高（億円）", "142", "189", "+33%"],
//    ["営業利益率", "18.2%", "22.7%", "+4.5pp"]]
// );
// slide.addTable(tableData, {
//   x: L.contentX, y: L.contentY, w: L.contentW,
//   colW: [3.0, 2.0, 2.0, 2.0],
//   border: { pt: 0.5, color: C.gridLine },
// });
```

---

## フレームワークコンポーネント

### 2×2 マトリクス

```javascript
function add2x2Matrix(slide, pres, {
  x, y, w, h,
  xAxisLabel, yAxisLabel,
  quadrants // [{ label, description, fill? }] — TL, TR, BL, BR 順
}) {
  const qw = (w - 0.05) / 2;  // 象限幅（ギャップ含む）
  const qh = (h - 0.05) / 2;  // 象限高さ

  const fills = [C.blue5, C.blue4, C.bgLight, C.blue3];
  const positions = [
    { qx: x, qy: y },                     // TL
    { qx: x + qw + 0.05, qy: y },         // TR
    { qx: x, qy: y + qh + 0.05 },         // BL
    { qx: x + qw + 0.05, qy: y + qh + 0.05 }, // BR
  ];

  quadrants.forEach((q, i) => {
    // 象限背景
    slide.addShape(pres.shapes.RECTANGLE, {
      x: positions[i].qx, y: positions[i].qy, w: qw, h: qh,
      fill: { color: q.fill || fills[i] },
      line: { color: C.gridLine, width: 0.5 }
    });

    // 象限ラベル
    slide.addText(q.label, {
      x: positions[i].qx + 0.15, y: positions[i].qy + 0.12,
      w: qw - 0.3, h: 0.35,
      fontFace: "Yu Mincho", fontSize: 11, bold: true,
      color: C.bgNavy, align: "left", valign: "top", margin: 0
    });

    // 象限説明
    if (q.description) {
      slide.addText(q.description, {
        x: positions[i].qx + 0.15, y: positions[i].qy + 0.5,
        w: qw - 0.3, h: qh - 0.65,
        fontFace: "Yu Gothic", fontSize: 9, color: C.textDark,
        align: "left", valign: "top", margin: 0
      });
    }
  });

  // X軸ラベル（下部中央）
  slide.addText(xAxisLabel, {
    x: x, y: y + h + 0.08, w: w, h: 0.25,
    fontFace: "Yu Gothic", fontSize: 9, bold: true,
    color: C.textDark, align: "center", margin: 0
  });

  // Y軸ラベル（左、回転）
  slide.addText(yAxisLabel, {
    x: x - 0.45, y: y, w: 0.35, h: h,
    fontFace: "Yu Gothic", fontSize: 9, bold: true,
    color: C.textDark, align: "center", valign: "middle",
    rotate: 270, margin: 0
  });
}
```

### 比較テーブル（Before/After）

コンサルティングでよく使われるBefore/After比較のためのコンポーネント。

```javascript
function addComparisonLayout(slide, pres, {
  leftTitle, leftItems, rightTitle, rightItems, y
}) {
  const colW = L.col2W;
  const leftX = L.contentX;
  const rightX = L.col2RightX;
  const startY = y || L.contentY;

  // 左カラムヘッダー
  slide.addShape(pres.shapes.RECTANGLE, {
    x: leftX, y: startY, w: colW, h: 0.4,
    fill: { color: C.blue4 }
  });
  slide.addText(leftTitle, {
    x: leftX + 0.1, y: startY, w: colW - 0.2, h: 0.4,
    fontFace: "Yu Mincho", fontSize: 12, bold: true,
    color: C.bgNavy, align: "center", valign: "middle", margin: 0
  });

  // 右カラムヘッダー
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: startY, w: colW, h: 0.4,
    fill: { color: C.royalBlue }
  });
  slide.addText(rightTitle, {
    x: rightX + 0.1, y: startY, w: colW - 0.2, h: 0.4,
    fontFace: "Yu Mincho", fontSize: 12, bold: true,
    color: C.textWhite, align: "center", valign: "middle", margin: 0
  });

  // 左カラム項目
  leftItems.forEach((item, i) => {
    const itemY = startY + 0.5 + i * 0.55;
    slide.addText(`● ${item}`, {
      x: leftX + 0.15, y: itemY, w: colW - 0.3, h: 0.45,
      fontFace: "Yu Gothic", fontSize: 10, color: C.textDark,
      align: "left", valign: "top", margin: 0
    });
  });

  // 右カラム項目
  rightItems.forEach((item, i) => {
    const itemY = startY + 0.5 + i * 0.55;
    slide.addText(`● ${item}`, {
      x: rightX + 0.15, y: itemY, w: colW - 0.3, h: 0.45,
      fontFace: "Yu Gothic", fontSize: 10, color: C.textDark,
      align: "left", valign: "top", margin: 0
    });
  });

  // 中央の矢印
  slide.addText("→", {
    x: leftX + colW, y: startY + 0.5, w: L.col2Gap, h: 0.5,
    fontFace: "Calibri", fontSize: 24, bold: true,
    color: C.royalBlue, align: "center", valign: "middle", margin: 0
  });
}
```

---

## ウォーターフォールチャート

PptxGenJSにはネイティブのウォーターフォールチャートがないため、積み上げ棒グラフとシェイプの組み合わせで構築する。

```javascript
function addWaterfallChart(slide, pres, {
  categories,   // ["開始", "成長A", "成長B", "減少C", "合計"]
  values,       // [100, 30, 20, -15, 135] ※合計は参考値
  x, y, w, h
}) {
  const chartX = x || L.contentX;
  const chartY = y || L.contentY;
  const chartW = w || L.contentW;
  const chartH = h || 3.0;

  // 値から積み上げ用の「透明ベース」と「表示バー」を計算
  let cumulative = 0;
  const bases = [];
  const positives = [];
  const negatives = [];

  values.forEach((val, i) => {
    if (i === 0) {
      // 開始値
      bases.push(0);
      positives.push(val);
      negatives.push(0);
      cumulative = val;
    } else if (i === values.length - 1) {
      // 合計
      bases.push(0);
      positives.push(cumulative);
      negatives.push(0);
    } else if (val >= 0) {
      bases.push(cumulative);
      positives.push(val);
      negatives.push(0);
      cumulative += val;
    } else {
      cumulative += val;
      bases.push(cumulative);
      positives.push(0);
      negatives.push(Math.abs(val));
    }
  });

  const chartData = [
    { name: "Base",     labels: categories, values: bases },
    { name: "Increase", labels: categories, values: positives },
    { name: "Decrease", labels: categories, values: negatives },
  ];

  slide.addChart(pres.charts.BAR, chartData, {
    x: chartX, y: chartY, w: chartW, h: chartH,
    barDir: "col",
    barGrouping: "stacked",
    chartColors: ["FFFFFF", C.royalBlue, C.accentRed],  // 透明ベース、青増加、赤減少
    chartArea: { fill: { color: C.bgWhite } },
    catAxisLabelColor: C.textDark,
    catAxisLabelFontFace: "Calibri",
    catAxisLabelFontSize: 9,
    valAxisLabelColor: C.textMuted,
    valAxisLabelFontFace: "Calibri",
    valAxisLabelFontSize: 9,
    valGridLine: { color: C.gridLine, size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: false,
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.textBlack,
    dataLabelFontFace: "Calibri",
    dataLabelFontSize: 9,
  });
}
```

注意: ウォーターフォールの透明ベースバーは`FFFFFF`（白）に設定されるため、白背景のスライドでのみ正常に動作する。ベースバーの値ラベルは手動で非表示にするか、データラベルのカスタマイズが必要。

---

## 再利用可能コードパターン

### 完全なスライドスクリプト骨格

```javascript
const pptxgen = require("pptxgenjs");

// === カラーパレット ===
const C = { /* ... 上記から貼り付け ... */ };

// === レイアウト定数 ===
const L = { /* ... 上記から貼り付け ... */ };

// === フォントファクトリ ===
const font = { /* ... 上記から貼り付け ... */ };

// === テンプレート関数 ===
// ... addTitleSlide, addContentSlide, etc.

// === プレゼンテーション構築 ===
async function buildDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "戦略チーム";
  pres.title = "分析プレゼンテーション";

  // スライド1: タイトル
  addTitleSlide(pres, {
    title: "市場分析 2025年度",
    subtitle: "戦略的評価と提言",
    date: "2025年2月"
  });

  // スライド2: エグゼクティブサマリー
  // ...

  // スライド3-N: 分析
  // ...

  // 保存
  await pres.writeFile({ fileName: "/home/claude/output.pptx" });
  console.log("プレゼンテーションを保存しました。");
}

buildDeck().catch(console.error);
```

### 重要な注意事項

1. **必ずファクトリ関数を使用する** — オプションオブジェクトを複数の`addShape`/`addText`呼び出しで再利用しないこと（PptxGenJSはオブジェクトをインプレースで変更する）。
2. **Hexカラーに`#`プレフィックスを使わない**。
3. **8文字Hexで透明度を指定しない** — `opacity`プロパティを使用する。
4. **アクションタイトルは文であり**、トピックラベルではない。
5. **全データスライドにソースラインが必要**。
6. **PDF変換でテストする** — LibreOfficeのレンダリングはPowerPointと異なる場合がある。
7. **日本語テキストの幅に注意** — 日本語は英語より文字幅が大きいため、テキストボックスの幅に余裕を持たせる。
8. **フォントフォールバックを考慮する** — 游明朝/游ゴシックが利用できない環境では代替フォントを用意する。

---

## 追加コンポーネント

### ドーナツチャート

構成比を5セグメント以下で表示する場合に使用。円グラフよりモダンな印象。

```javascript
function addConsultingDonutChart(slide, pres, { chartData, x, y, w, h }) {
  slide.addChart(pres.charts.DOUGHNUT, chartData, {
    x: x || L.contentX + 1.5,
    y: y || L.contentY + 0.2,
    w: w || 3.5,
    h: h || 3.0,
    chartColors: [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5],
    chartArea: { fill: { color: C.bgWhite } },
    holeSize: 55,
    showLegend: true,
    legendPos: "b",
    legendFontFace: "Calibri",
    legendFontSize: 9,
    legendColor: C.textDark,
    showPercent: true,
    showValue: false,
    showTitle: false,
    dataLabelColor: C.textBlack,
    dataLabelFontFace: "Calibri",
    dataLabelFontSize: 10,
    dataLabelPosition: "outEnd",
  });
}
```

### プロセスフロー

3〜5ステップの手順やワークフローを矢印付きで図示する。

```javascript
function addProcessFlow(slide, pres, {
  steps, // [{ title, description }]
  y
}) {
  const startY = y || L.contentY + 0.3;
  const count = steps.length;
  const stepW = (L.contentW - (count - 1) * 0.6) / count;
  const stepH = 1.8;
  const colors = [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5];

  steps.forEach((step, i) => {
    const stepX = L.contentX + i * (stepW + 0.6);

    // ステップカード
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: stepX, y: startY, w: stepW, h: stepH,
      fill: { color: C.bgLight },
      line: { color: colors[i] || C.blue3, width: 1.0 },
      rectRadius: 0.06
    });

    // ステップ番号ヘッダー
    slide.addShape(pres.shapes.RECTANGLE, {
      x: stepX + 0.01, y: startY + 0.01, w: stepW - 0.02, h: 0.45,
      fill: { color: colors[i] || C.blue3 },
    });

    slide.addText(`Step ${i + 1}`, {
      x: stepX, y: startY + 0.02, w: stepW, h: 0.25,
      fontFace: "Calibri", fontSize: 9, color: C.textWhite,
      align: "center", valign: "middle", margin: 0
    });

    slide.addText(step.title, {
      x: stepX + 0.1, y: startY + 0.25, w: stepW - 0.2, h: 0.22,
      fontFace: "Yu Gothic", fontSize: 10, bold: true,
      color: C.textWhite, align: "center", valign: "middle", margin: 0
    });

    // 説明テキスト
    if (step.description) {
      slide.addText(step.description, {
        x: stepX + 0.1, y: startY + 0.55, w: stepW - 0.2, h: stepH - 0.7,
        fontFace: "Yu Gothic", fontSize: 9, color: C.textDark,
        align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.3
      });
    }

    // 矢印（最後のステップ以外）
    if (i < count - 1) {
      slide.addText("→", {
        x: stepX + stepW, y: startY + stepH / 2 - 0.2, w: 0.6, h: 0.4,
        fontFace: "Calibri", fontSize: 22, bold: true,
        color: C.royalBlue, align: "center", valign: "middle", margin: 0
      });
    }
  });
}
```

### ファネル

段階的な絞り込み、コンバージョンパイプラインの図示。

```javascript
function addFunnel(slide, pres, {
  stages, // [{ label, value, percentage }]
  x, y, w, h
}) {
  const funnelX = x || L.contentX + 0.5;
  const funnelY = y || L.contentY + 0.2;
  const funnelW = w || 7.0;
  const funnelH = h || 3.2;
  const stageH = funnelH / stages.length;
  const colors = [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5];

  stages.forEach((stage, i) => {
    // 幅を段階的に狭くする
    const widthRatio = 1 - (i * 0.18);
    const stageW = funnelW * widthRatio;
    const stageX = funnelX + (funnelW - stageW) / 2;
    const stageY = funnelY + i * (stageH + 0.08);

    // ステージ矩形
    slide.addShape(pres.shapes.RECTANGLE, {
      x: stageX, y: stageY, w: stageW, h: stageH - 0.1,
      fill: { color: colors[i] || C.blue5 },
      line: { color: C.bgWhite, width: 1.0 }
    });

    // ラベル＋値
    const labelText = stage.percentage
      ? `${stage.label}  (${stage.percentage})`
      : stage.label;
    slide.addText(labelText, {
      x: stageX + 0.15, y: stageY, w: stageW - 0.3, h: stageH - 0.1,
      fontFace: "Yu Gothic", fontSize: 11, bold: true,
      color: C.textWhite, align: "center", valign: "middle", margin: 0
    });

    // 右側に値表示
    if (stage.value) {
      slide.addText(stage.value, {
        x: stageX + stageW + 0.2, y: stageY, w: 1.5, h: stageH - 0.1,
        fontFace: "Calibri", fontSize: 12, bold: true,
        color: C.textDark, align: "left", valign: "middle", margin: 0
      });
    }
  });
}
```

### SWOT分析マトリクス

4象限のSWOT分析を表示する特殊化された2x2マトリクス。

```javascript
function addSWOTMatrix(slide, pres, {
  x, y, w, h,
  strengths, weaknesses, opportunities, threats
}) {
  const matX = x || L.contentX + 0.5;
  const matY = y || L.contentY;
  const matW = w || 8.0;
  const matH = h || 3.4;
  const qw = (matW - 0.06) / 2;
  const qh = (matH - 0.06) / 2;

  const quadrants = [
    { label: "強み (Strengths)", items: strengths, fill: C.blue5, headerFill: C.royalBlue },
    { label: "弱み (Weaknesses)", items: weaknesses, fill: "FFF3E0", headerFill: "E65100" },
    { label: "機会 (Opportunities)", items: opportunities, fill: "E8F5E9", headerFill: C.accentGreen },
    { label: "脅威 (Threats)", items: threats, fill: "FFEBEE", headerFill: C.accentRed },
  ];

  const positions = [
    { qx: matX, qy: matY },
    { qx: matX + qw + 0.06, qy: matY },
    { qx: matX, qy: matY + qh + 0.06 },
    { qx: matX + qw + 0.06, qy: matY + qh + 0.06 },
  ];

  quadrants.forEach((q, i) => {
    // 象限背景
    slide.addShape(pres.shapes.RECTANGLE, {
      x: positions[i].qx, y: positions[i].qy, w: qw, h: qh,
      fill: { color: q.fill },
      line: { color: C.gridLine, width: 0.5 }
    });

    // ヘッダーバー
    slide.addShape(pres.shapes.RECTANGLE, {
      x: positions[i].qx, y: positions[i].qy, w: qw, h: 0.32,
      fill: { color: q.headerFill },
    });

    slide.addText(q.label, {
      x: positions[i].qx + 0.1, y: positions[i].qy, w: qw - 0.2, h: 0.32,
      fontFace: "Yu Gothic", fontSize: 10, bold: true,
      color: C.textWhite, align: "left", valign: "middle", margin: 0
    });

    // 項目リスト
    const itemsText = q.items.map(item => `● ${item}`).join("\n");
    slide.addText(itemsText, {
      x: positions[i].qx + 0.12, y: positions[i].qy + 0.38,
      w: qw - 0.24, h: qh - 0.45,
      fontFace: "Yu Gothic", fontSize: 9, color: C.textDark,
      align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.4
    });
  });
}
```

### ヒートマップ風テーブル

セルの値に応じて背景色の濃度を変えるテーブル。パフォーマンス評価やスコアリングに適用。

```javascript
function buildHeatmapTable(headers, rows, {
  valueColumns, // 値が入る列のインデックス配列
  thresholds    // { high: 80, mid: 50 } 閾値
}) {
  const headerCells = headers.map(h => ({
    text: h,
    options: {
      fill: { color: C.bgNavy },
      color: C.textWhite,
      fontFace: "Yu Gothic",
      fontSize: 10,
      bold: true,
      align: "center",
      valign: "middle",
      border: { pt: 0.5, color: C.gridLine },
      margin: [4, 6, 4, 6],
    }
  }));

  const dataRows = rows.map((row) => {
    return row.map((cell, colIdx) => {
      let fillColor = C.bgWhite;
      if (valueColumns && valueColumns.includes(colIdx)) {
        const numVal = parseFloat(String(cell).replace(/[^0-9.-]/g, ""));
        if (!isNaN(numVal)) {
          if (numVal >= (thresholds?.high || 80)) fillColor = "C8E6C9";      // 緑系
          else if (numVal >= (thresholds?.mid || 50)) fillColor = C.blue5;    // 薄い青
          else fillColor = "FFCDD2";                                          // 赤系
        }
      }

      return {
        text: String(cell),
        options: {
          fill: { color: fillColor },
          color: C.textDark,
          fontFace: colIdx === 0 ? "Yu Gothic" : "Calibri",
          fontSize: 10,
          bold: valueColumns?.includes(colIdx) || false,
          align: colIdx === 0 ? "left" : "center",
          valign: "middle",
          border: { pt: 0.5, color: C.gridLine },
          margin: [3, 6, 3, 6],
        }
      };
    });
  });

  return [headerCells, ...dataRows];
}
```
