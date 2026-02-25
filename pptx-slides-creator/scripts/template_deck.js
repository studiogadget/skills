/**
 * スライドデッキ テンプレート
 *
 * 新しいプレゼンテーションを作成する際のスターターコード。
 * すべてのデザインシステム定数・テンプレート関数を含む。
 *
 * 使い方:
 *   1. このファイルをコピーして名前を変更する
 *   2. buildDeck() 内のスライドを編集する
 *   3. `node <ファイル名>.js` で実行
 *
 * 前提: npm install pptxgenjs が完了していること
 */

const pptxgen = require("pptxgenjs");

// ========================================
// カラーパレット
// ========================================
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

// ========================================
// レイアウト定数
// ========================================
const L = {
  // マージン
  mx: 0.5,
  my: 0.5,

  // コンテンツエリア
  contentX: 0.5,
  contentY: 1.2,
  contentW: 9.0,         // 10 - 2*0.5
  contentH: 3.6,

  // タイトル
  titleX: 0.5,
  titleY: 0.42,
  titleW: 9.0,
  titleH: 0.55,
  dividerY: 1.02,

  // フッター
  sourceX: 0.5,
  sourceY: 5.15,
  pageNumX: 9.0,
  pageNumY: 5.15,

  // カラムヘルパー
  col2W: 4.3,
  col2Gap: 0.4,
  col2RightX: 5.2,       // 0.5 + 4.3 + 0.4

  col3W: 2.73,
  col3Gap: 0.4,
  col3MidX: 3.63,
  col3RightX: 6.76,
};

// ========================================
// フォントファクトリ（常に新しいオブジェクトを生成）
// ========================================
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
  bodySmall: () => ({
    fontFace: "Yu Gothic", fontSize: 10, color: C.textDark, margin: 0
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

// ========================================
// テンプレート関数
// ========================================

/**
 * タイトルスライド（ダークネイビー背景）
 */
function addTitleSlide(pres, { title, subtitle, date }) {
  const slide = pres.addSlide();
  slide.background = { color: C.bgNavy };

  slide.addText(title, {
    x: 0.8, y: 1.4, w: 8.4, h: 1.3,
    fontFace: "Yu Mincho", fontSize: 30, bold: true,
    color: C.textWhite, align: "left", valign: "middle", margin: 0
  });

  slide.addShape(pres.shapes.LINE, {
    x: 0.8, y: 2.85, w: 2.0, h: 0,
    line: { color: C.textWhite, width: 1.0 }
  });

  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.8, y: 3.1, w: 8.4, h: 0.7,
      fontFace: "Yu Gothic", fontSize: 14, color: C.blue3,
      align: "left", valign: "top", margin: 0
    });
  }

  if (date) {
    slide.addText(date, {
      x: 0.8, y: 4.6, w: 8.4, h: 0.3,
      fontFace: "Calibri", fontSize: 10, color: C.blue4,
      align: "left", margin: 0
    });
  }

  return slide;
}

/**
 * 標準コンテンツスライド
 * アクションタイトル + ディバイダー + ソース + ページ番号
 */
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

/**
 * KPIコールアウト行
 * kpis: [{ value, label, delta? }]
 */
function addKPIRow(slide, pres, kpis, { y }) {
  const count = kpis.length;
  const kpiW = L.contentW / count;

  kpis.forEach((kpi, i) => {
    const kpiX = L.contentX + i * kpiW;

    slide.addText(kpi.value, {
      x: kpiX, y: y, w: kpiW, h: 0.65,
      ...font.calloutNum(), align: "center", valign: "bottom"
    });

    slide.addText(kpi.label, {
      x: kpiX, y: y + 0.68, w: kpiW, h: 0.25,
      ...font.calloutLabel(), align: "center", valign: "top"
    });

    if (kpi.delta) {
      const isPositive = kpi.delta.startsWith("+");
      slide.addText(kpi.delta, {
        x: kpiX, y: y + 0.95, w: kpiW, h: 0.2,
        fontFace: "Calibri", fontSize: 9, bold: true,
        color: isPositive ? C.accentGreen : C.accentRed,
        align: "center", margin: 0
      });
    }

    if (i < count - 1) {
      slide.addShape(pres.shapes.LINE, {
        x: kpiX + kpiW, y: y + 0.1, w: 0, h: 0.95,
        line: { color: C.gridLine, width: 0.5 }
      });
    }
  });
}

/**
 * コンサルティンググレード データテーブル
 */
function buildConsultingTable(headers, rows) {
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

  const dataRows = rows.map((row, rowIdx) => {
    return row.map((cell, colIdx) => ({
      text: String(cell),
      options: {
        fill: { color: rowIdx % 2 === 0 ? C.bgWhite : C.bgLight },
        color: C.textDark,
        fontFace: colIdx === 0 ? "Yu Gothic" : "Calibri",
        fontSize: 10,
        align: colIdx === 0 ? "left" : "right",
        valign: "middle",
        border: { pt: 0.5, color: C.gridLine },
        margin: [3, 6, 3, 6],
      }
    }));
  });

  return [headerCells, ...dataRows];
}

/**
 * 棒グラフ（カラムチャート）
 */
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

/**
 * 積み上げ棒グラフ
 */
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

/**
 * 折れ線グラフ
 */
function addConsultingLineChart(slide, pres, { chartData, x, y, w, h }) {
  slide.addChart(pres.charts.LINE, chartData, {
    x: x || L.contentX, y: y || L.contentY,
    w: w || L.contentW, h: h || 3.2,
    lineSize: 2,
    lineSmooth: false,
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

/**
 * ドーナツチャート（5セグメント以下の構成比表示）
 */
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

/**
 * ウォーターフォールチャート
 */
function addWaterfallChart(slide, pres, { categories, values, x, y, w, h }) {
  const chartX = x || L.contentX;
  const chartY = y || L.contentY;
  const chartW = w || L.contentW;
  const chartH = h || 3.0;

  let cumulative = 0;
  const bases = [];
  const positives = [];
  const negatives = [];

  values.forEach((val, i) => {
    if (i === 0) {
      bases.push(0);
      positives.push(val);
      negatives.push(0);
      cumulative = val;
    } else if (i === values.length - 1) {
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

  slide.addChart(pres.charts.BAR, [
    { name: "Base",     labels: categories, values: bases },
    { name: "Increase", labels: categories, values: positives },
    { name: "Decrease", labels: categories, values: negatives },
  ], {
    x: chartX, y: chartY, w: chartW, h: chartH,
    barDir: "col",
    barGrouping: "stacked",
    chartColors: ["FFFFFF", C.royalBlue, C.accentRed],
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

/**
 * 2x2 マトリクス
 */
function add2x2Matrix(slide, pres, {
  x, y, w, h, xAxisLabel, yAxisLabel,
  quadrants // [{ label, description, fill? }] — TL, TR, BL, BR 順
}) {
  const qw = (w - 0.05) / 2;
  const qh = (h - 0.05) / 2;
  const fills = [C.blue5, C.blue4, C.bgLight, C.blue3];
  const positions = [
    { qx: x, qy: y },
    { qx: x + qw + 0.05, qy: y },
    { qx: x, qy: y + qh + 0.05 },
    { qx: x + qw + 0.05, qy: y + qh + 0.05 },
  ];

  quadrants.forEach((q, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: positions[i].qx, y: positions[i].qy, w: qw, h: qh,
      fill: { color: q.fill || fills[i] },
      line: { color: C.gridLine, width: 0.5 }
    });

    slide.addText(q.label, {
      x: positions[i].qx + 0.15, y: positions[i].qy + 0.12,
      w: qw - 0.3, h: 0.35,
      fontFace: "Yu Mincho", fontSize: 11, bold: true,
      color: C.bgNavy, align: "left", valign: "top", margin: 0
    });

    if (q.description) {
      slide.addText(q.description, {
        x: positions[i].qx + 0.15, y: positions[i].qy + 0.5,
        w: qw - 0.3, h: qh - 0.65,
        fontFace: "Yu Gothic", fontSize: 9, color: C.textDark,
        align: "left", valign: "top", margin: 0
      });
    }
  });

  slide.addText(xAxisLabel, {
    x: x, y: y + h + 0.08, w: w, h: 0.25,
    fontFace: "Yu Gothic", fontSize: 9, bold: true,
    color: C.textDark, align: "center", margin: 0
  });

  slide.addText(yAxisLabel, {
    x: x - 0.45, y: y, w: 0.35, h: h,
    fontFace: "Yu Gothic", fontSize: 9, bold: true,
    color: C.textDark, align: "center", valign: "middle",
    rotate: 270, margin: 0
  });
}

/**
 * 比較レイアウト（Before/After）
 */
function addComparisonLayout(slide, pres, {
  leftTitle, leftItems, rightTitle, rightItems, y
}) {
  const colW = L.col2W;
  const leftX = L.contentX;
  const rightX = L.col2RightX;
  const startY = y || L.contentY;

  slide.addShape(pres.shapes.RECTANGLE, {
    x: leftX, y: startY, w: colW, h: 0.4,
    fill: { color: C.blue4 }
  });
  slide.addText(leftTitle, {
    x: leftX + 0.1, y: startY, w: colW - 0.2, h: 0.4,
    fontFace: "Yu Mincho", fontSize: 12, bold: true,
    color: C.bgNavy, align: "center", valign: "middle", margin: 0
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: startY, w: colW, h: 0.4,
    fill: { color: C.royalBlue }
  });
  slide.addText(rightTitle, {
    x: rightX + 0.1, y: startY, w: colW - 0.2, h: 0.4,
    fontFace: "Yu Mincho", fontSize: 12, bold: true,
    color: C.textWhite, align: "center", valign: "middle", margin: 0
  });

  leftItems.forEach((item, i) => {
    const itemY = startY + 0.5 + i * 0.55;
    slide.addText(`● ${item}`, {
      x: leftX + 0.15, y: itemY, w: colW - 0.3, h: 0.45,
      fontFace: "Yu Gothic", fontSize: 10, color: C.textDark,
      align: "left", valign: "top", margin: 0
    });
  });

  rightItems.forEach((item, i) => {
    const itemY = startY + 0.5 + i * 0.55;
    slide.addText(`● ${item}`, {
      x: rightX + 0.15, y: itemY, w: colW - 0.3, h: 0.45,
      fontFace: "Yu Gothic", fontSize: 10, color: C.textDark,
      align: "left", valign: "top", margin: 0
    });
  });

  slide.addText("→", {
    x: leftX + colW, y: startY + 0.5, w: L.col2Gap, h: 0.5,
    fontFace: "Calibri", fontSize: 24, bold: true,
    color: C.royalBlue, align: "center", valign: "middle", margin: 0
  });
}

/**
 * プロセスフロー（3〜5ステップ）
 */
function addProcessFlow(slide, pres, { steps, y }) {
  const startY = y || L.contentY + 0.3;
  const count = steps.length;
  const stepW = (L.contentW - (count - 1) * 0.6) / count;
  const stepH = 1.8;
  const colors = [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5];

  steps.forEach((step, i) => {
    const stepX = L.contentX + i * (stepW + 0.6);

    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: stepX, y: startY, w: stepW, h: stepH,
      fill: { color: C.bgLight },
      line: { color: colors[i] || C.blue3, width: 1.0 },
      rectRadius: 0.06
    });

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

    if (step.description) {
      slide.addText(step.description, {
        x: stepX + 0.1, y: startY + 0.55, w: stepW - 0.2, h: stepH - 0.7,
        fontFace: "Yu Gothic", fontSize: 9, color: C.textDark,
        align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.3
      });
    }

    if (i < count - 1) {
      slide.addText("→", {
        x: stepX + stepW, y: startY + stepH / 2 - 0.2, w: 0.6, h: 0.4,
        fontFace: "Calibri", fontSize: 22, bold: true,
        color: C.royalBlue, align: "center", valign: "middle", margin: 0
      });
    }
  });
}

/**
 * ファネル
 */
function addFunnel(slide, pres, { stages, x, y, w, h }) {
  const funnelX = x || L.contentX + 0.5;
  const funnelY = y || L.contentY + 0.2;
  const funnelW = w || 7.0;
  const funnelH = h || 3.2;
  const gap = 0.08;
  const n = stages.length;
  const stageH = n > 0 ? (funnelH - gap * (n - 1)) / n : 0;
  const colors = [C.royalBlue, C.blue2, C.blue3, C.blue4, C.blue5];
  stages.forEach((stage, i) => {
    const widthRatio = 1 - (i * 0.18);
    const stageW = funnelW * widthRatio;
    const stageX = funnelX + (funnelW - stageW) / 2;
    const stageY = funnelY + i * (stageH + gap);

    slide.addShape(pres.shapes.RECTANGLE, {
      x: stageX, y: stageY, w: stageW, h: stageH - 0.1,
      fill: { color: colors[i] || C.blue5 },
      line: { color: C.bgWhite, width: 1.0 }
    });

    const labelText = stage.percentage
      ? `${stage.label}  (${stage.percentage})`
      : stage.label;
    slide.addText(labelText, {
      x: stageX + 0.15, y: stageY, w: stageW - 0.3, h: stageH - 0.1,
      fontFace: "Yu Gothic", fontSize: 11, bold: true,
      color: C.textWhite, align: "center", valign: "middle", margin: 0
    });

    if (stage.value) {
      slide.addText(stage.value, {
        x: stageX + stageW + 0.2, y: stageY, w: 1.5, h: stageH - 0.1,
        fontFace: "Calibri", fontSize: 12, bold: true,
        color: C.textDark, align: "left", valign: "middle", margin: 0
      });
    }
  });
}

// ========================================
// プレゼンテーション構築
// ========================================
async function buildDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "戦略チーム";
  pres.title = "プレゼンテーションタイトル";

  // ─── スライド1: タイトル ───
  addTitleSlide(pres, {
    title: "プレゼンテーションタイトル",
    subtitle: "サブタイトル — 目的を1行で述べる",
    date: "2026年2月"
  });

  // ─── スライド2: エグゼクティブサマリー（KPIコールアウト＋発見事項） ───
  const slide2 = addContentSlide(pres, {
    actionTitle: "【アクションタイトル: 主要な洞察を1文で述べる】",
    sourceText: "出典を記載",
    pageNum: 1
  });

  addKPIRow(slide2, pres, [
    { value: "XX%", label: "指標ラベル1", delta: "+X.Xpp" },
    { value: "¥XXX億", label: "指標ラベル2" },
    { value: "XX", label: "指標ラベル3" },
  ], { y: L.contentY });

  // ─── スライド3: データ分析（チャート＋テキスト） ───
  const slide3 = addContentSlide(pres, {
    actionTitle: "【アクションタイトル: データから読み取れる洞察を述べる】",
    sourceText: "出典を記載",
    pageNum: 2
  });

  // チャートを左、テキストを右に配置
  // addConsultingBarChart(slide3, pres, {
  //   chartData: [{ name: "系列名", labels: [...], values: [...] }],
  //   x: L.contentX, y: L.contentY, w: 5.0, h: 3.2
  // });

  // ─── スライド4: フレームワーク（2x2マトリクス） ───
  // const slide4 = addContentSlide(pres, { ... });
  // add2x2Matrix(slide4, pres, { ... });

  // ─── スライド5: 比較テーブル ───
  // const slide5 = addContentSlide(pres, { ... });
  // const tableData = buildConsultingTable([...], [...]);
  // slide5.addTable(tableData, { ... });

  // ─── スライドN: 示唆・提言 ───
  // const slideN = addContentSlide(pres, { ... });

  // ─── 保存 ───
  const outputPath = "./output.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log(`プレゼンテーションを保存しました: ${outputPath}`);
}

buildDeck().catch(console.error);
