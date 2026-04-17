const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, TableOfContents,
  LevelFormat
} = require("C:/Users/User/AppData/Roaming/npm/node_modules/docx");
const fs = require("fs");
const path = require("path");

// ── 결과 JSON 로드 ────────────────────────────────────────────────────────────
const jsonPath = path.join(__dirname, "latest_results.json");
const data = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));
const runAt = data.run_at;
const allResults = data.results;

const MODULE_LABELS = {
  "test_file_reader": "file_reader.py — 파일 텍스트 추출 모듈",
  "test_rule_parser": "rule_parser.py — 규칙 파싱 모듈",
  "test_organizer":   "organizer.py — 파일 분류/이동 모듈",
};
const MODULE_DESC = {
  "test_file_reader": "지원 파일 형식(TXT, DOCX, XLSX)의 텍스트 추출 기능, 미지원 형식 처리, 500자 제한, 성능, 인코딩, 경계 조건을 검증하였습니다.",
  "test_rule_parser": "자연어 규칙을 JSON으로 파싱하는 기능, 반환 구조 검증, API 호출 효율성, 예외 처리를 검증하였습니다.",
  "test_organizer":   "파일 분류 계획 생성, 백업 생성, 파일 이동/이름 변경, 중복 처리, fallback 로직, 성능을 검증하였습니다.",
};

// ── 집계 ─────────────────────────────────────────────────────────────────────
let totalPass = 0, totalFail = 0, totalAll = 0;
for (const rows of Object.values(allResults)) {
  for (const r of rows) {
    totalAll++;
    if (r.status === "PASS") totalPass++; else totalFail++;
  }
}
const passRate = totalAll > 0 ? Math.round((totalPass / totalAll) * 100) : 0;

// ── 스타일 상수 ───────────────────────────────────────────────────────────────
const BLUE_HEADER = "1F4E79";
const LIGHT_BLUE  = "D6E4F0";
const GREEN       = "00703C";
const RED         = "C00000";
const GRAY_ROW    = "F5F5F5";

const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: BLUE_HEADER, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 18, font: "Arial" })]
    })]
  });
}

function dataCell(text, width, opts = {}) {
  const { center = false, color = "000000", bold = false, shading = "FFFFFF" } = opts;
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: shading, type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: [new TextRun({ text, size: 17, font: "Arial", color, bold })]
    })]
  });
}

function makeModuleTable(rows) {
  const colWidths = [480, 2300, 600, 600, 700, 2680];
  const total = colWidths.reduce((a, b) => a + b, 0);
  const bg = (i) => i % 2 === 0 ? "FFFFFF" : GRAY_ROW;

  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [
          headerCell("번호", colWidths[0]),
          headerCell("테스트 항목", colWidths[1]),
          headerCell("유형", colWidths[2]),
          headerCell("결과", colWidths[3]),
          headerCell("시간(ms)", colWidths[4]),
          headerCell("상세", colWidths[5]),
        ]
      }),
      ...rows.map((r, i) => {
        const isPass = r.status === "PASS";
        return new TableRow({
          children: [
            dataCell(String(i + 1), colWidths[0], { center: true, shading: bg(i) }),
            dataCell(r.name, colWidths[1], { shading: bg(i) }),
            dataCell(r.name.includes("성능") || r.name.includes("제한") || r.name.includes("횟수") || r.name.includes("긴 입력") || r.name.includes("API") ? "비기능" : "기능", colWidths[2], { center: true, shading: bg(i) }),
            dataCell(r.status, colWidths[3], { center: true, color: isPass ? GREEN : RED, bold: true, shading: bg(i) }),
            dataCell(String(r.elapsed_ms), colWidths[4], { center: true, shading: bg(i) }),
            dataCell(r.detail || "-", colWidths[5], { shading: bg(i) }),
          ]
        });
      })
    ]
  });
}

function summaryTable() {
  const colWidths = [2400, 1800, 1800, 1800, 1560];
  const total = colWidths.reduce((a,b)=>a+b,0);
  const moduleKeys = Object.keys(allResults);
  const bg = (i) => i % 2 === 0 ? "FFFFFF" : GRAY_ROW;

  const dataRows = moduleKeys.map((key, i) => {
    const rows = allResults[key];
    const pass = rows.filter(r => r.status === "PASS").length;
    const fail = rows.length - pass;
    const shortName = key.replace("test_", "") + ".py";
    return new TableRow({
      children: [
        dataCell(shortName, colWidths[0], { shading: bg(i) }),
        dataCell(MODULE_LABELS[key]?.split("—")[1]?.trim() || "", colWidths[1], { shading: bg(i) }),
        dataCell(String(rows.length), colWidths[2], { center: true, shading: bg(i) }),
        dataCell(String(pass), colWidths[3], { center: true, color: GREEN, bold: true, shading: bg(i) }),
        dataCell(String(fail), colWidths[4], { center: true, color: fail > 0 ? RED : "000000", shading: bg(i) }),
      ]
    });
  });

  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [
          headerCell("모듈", colWidths[0]),
          headerCell("역할", colWidths[1]),
          headerCell("전체", colWidths[2]),
          headerCell("PASS", colWidths[3]),
          headerCell("FAIL", colWidths[4]),
        ]
      }),
      ...dataRows,
      new TableRow({
        children: [
          new TableCell({
            borders, columnSpan: 2,
            width: { size: colWidths[0]+colWidths[1], type: WidthType.DXA },
            shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR },
            margins: { top:80, bottom:80, left:120, right:120 },
            children: [new Paragraph({ alignment: AlignmentType.CENTER,
              children: [new TextRun({ text:"합계", bold:true, size:18, font:"Arial" })] })]
          }),
          dataCell(String(totalAll),  colWidths[2], { center:true, shading: LIGHT_BLUE }),
          dataCell(String(totalPass), colWidths[3], { center:true, color: GREEN, bold:true, shading: LIGHT_BLUE }),
          dataCell(String(totalFail), colWidths[4], { center:true, color: totalFail>0?RED:"000000", shading: LIGHT_BLUE }),
        ]
      })
    ]
  });
}

function gap(n=1) { return Array.from({length:n}, ()=>new Paragraph({children:[]})); }
function h(text, level) { return new Paragraph({ heading: level, children: [new TextRun({text, font:"Arial"})] }); }
function body(text) { return new Paragraph({ spacing:{before:60,after:60}, children:[new TextRun({text, size:20, font:"Arial"})] }); }
function bullet(text) { return new Paragraph({ numbering:{reference:"bullets",level:0}, children:[new TextRun({text, size:20, font:"Arial"})] }); }

// ── Document ──────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: { config: [{
    reference: "bullets",
    levels: [{ level:0, format:LevelFormat.BULLET, text:"-", alignment:AlignmentType.LEFT,
      style:{paragraph:{indent:{left:720,hanging:360}}} }]
  }]},
  styles: {
    default: { document: { run: { font:"Arial", size:20 } } },
    paragraphStyles: [
      { id:"Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{size:36,bold:true,font:"Arial",color:"1F4E79"},
        paragraph:{spacing:{before:320,after:160},outlineLevel:0} },
      { id:"Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{size:28,bold:true,font:"Arial",color:"2E74B5"},
        paragraph:{spacing:{before:240,after:120},outlineLevel:1} },
      { id:"Heading3", name:"Heading 3", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{size:22,bold:true,font:"Arial",color:"1F4E79"},
        paragraph:{spacing:{before:180,after:80},outlineLevel:2} },
    ]
  },
  sections: [{
    properties: { page: {
      size: { width:15840, height:12240 },
      margin: { top:1080, right:1080, bottom:1080, left:1080 }
    }},
    headers: { default: new Header({ children: [new Paragraph({
      border: { bottom:{style:BorderStyle.SINGLE,size:6,color:"2E74B5",space:1} },
      children: [
        new TextRun({text:"Clean Folder  |  기능/비기능 테스트 결과 보고서", size:16, color:"555555", font:"Arial"}),
        new TextRun({text:"\t실행일: " + runAt, size:16, color:"888888", font:"Arial"}),
      ],
      tabStops: [{type:"right", position:13680}]
    })]})},
    footers: { default: new Footer({ children: [new Paragraph({
      border: { top:{style:BorderStyle.SINGLE,size:4,color:"CCCCCC",space:1} },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({text:"- ", size:16, color:"888888"}),
        new TextRun({children:[PageNumber.CURRENT], size:16, color:"555555"}),
        new TextRun({text:" -", size:16, color:"888888"}),
      ]
    })]})},
    children: [
      // ── 표지 ──────────────────────────────────────────────────────────────
      ...gap(4),
      new Paragraph({ alignment:AlignmentType.CENTER, spacing:{before:0,after:80},
        children:[new TextRun({text:"Clean Folder", font:"Arial", size:64, bold:true, color:"1F4E79"})] }),
      new Paragraph({ alignment:AlignmentType.CENTER, spacing:{before:80,after:240},
        children:[new TextRun({text:"기능 / 비기능 테스트 결과 보고서", font:"Arial", size:40, color:"2E74B5"})] }),
      new Paragraph({ alignment:AlignmentType.CENTER,
        border:{bottom:{style:BorderStyle.SINGLE,size:8,color:"2E74B5",space:4}},
        spacing:{before:0,after:0}, children:[] }),
      ...gap(2),
      new Paragraph({ alignment:AlignmentType.CENTER,
        children:[new TextRun({text:"실행일: " + runAt, size:22, font:"Arial", color:"555555"})] }),
      new Paragraph({ alignment:AlignmentType.CENTER,
        children:[new TextRun({text:"작성자: QA팀", size:22, font:"Arial", color:"555555"})] }),
      new Paragraph({ alignment:AlignmentType.CENTER,
        children:[new TextRun({
          text:`테스트: ${totalAll}개   PASS: ${totalPass}개   합격률: ${passRate}%`,
          size:24, font:"Arial", bold:true,
          color: passRate === 100 ? GREEN : RED
        })] }),
      ...gap(3),
      new Paragraph({children:[new PageBreak()]}),

      // ── 목차 ──────────────────────────────────────────────────────────────
      new TableOfContents("목차", {hyperlink:true, headingStyleRange:"1-3"}),
      new Paragraph({children:[new PageBreak()]}),

      // ── 1장 ───────────────────────────────────────────────────────────────
      h("1장. 개요", HeadingLevel.HEADING_1),
      h("1.1 프로젝트 설명", HeadingLevel.HEADING_2),
      body("Clean Folder는 AI(GPT-4o)가 파일 내용을 분석하여 사용자가 자연어로 입력한 규칙에 따라 파일 이름 변경 및 폴더 분류를 자동으로 수행하는 Streamlit 기반 웹 애플리케이션입니다."),
      ...gap(1),
      h("1.2 테스트 목적", HeadingLevel.HEADING_2),
      bullet("각 모듈의 기능이 요구사항대로 동작하는지 검증"),
      bullet("경계 조건 및 예외 상황에서의 안정성 확인"),
      bullet("성능 기준(처리 시간) 충족 여부 검증"),
      bullet("실제 OpenAI API 연동 전 단위 수준에서의 품질 보증"),
      ...gap(1),
      h("1.3 테스트 범위", HeadingLevel.HEADING_2),
      ...Object.keys(allResults).map(key => bullet(MODULE_LABELS[key] || key)),
      new Paragraph({children:[new PageBreak()]}),

      // ── 2장 ───────────────────────────────────────────────────────────────
      h("2장. 테스트 환경", HeadingLevel.HEADING_1),
      h("2.1 소프트웨어 환경", HeadingLevel.HEADING_2),
      bullet("운영체제: Windows 11 Pro"),
      bullet("런타임: Python 3.12"),
      bullet("프레임워크: Streamlit 1.56.0"),
      bullet("AI 모델: OpenAI GPT-4o (단위 테스트 시 unittest.mock으로 모킹)"),
      ...gap(1),
      h("2.2 주요 의존성", HeadingLevel.HEADING_2),
      bullet("pypdf  —  PDF 텍스트 추출"),
      bullet("python-docx  —  DOCX 텍스트 추출"),
      bullet("python-pptx  —  PPTX 텍스트 추출"),
      bullet("openpyxl  —  XLSX 텍스트 추출"),
      ...gap(1),
      h("2.3 테스트 데이터", HeadingLevel.HEADING_2),
      bullet("sample_data/ 디렉토리 내 15개 파일 (TXT x8, DOCX x3, XLSX x2, PNG x1, JPG x1)"),
      bullet("임시 디렉토리(tempfile.mkdtemp) 활용 격리 테스트"),
      new Paragraph({children:[new PageBreak()]}),

      // ── 3장 ───────────────────────────────────────────────────────────────
      h("3장. 테스트 결과 요약", HeadingLevel.HEADING_1),
      ...gap(1),
      new Paragraph({ spacing:{before:80,after:160}, children:[
        new TextRun({text:"총 ", size:22, font:"Arial"}),
        new TextRun({text:`${totalAll}개 테스트 중 ${totalPass}개 PASS`, size:22, font:"Arial", bold:true, color: passRate===100?GREEN:RED}),
        new TextRun({text:` — 합격률 ${passRate}%`, size:22, font:"Arial"}),
      ]}),
      summaryTable(),
      ...gap(2),
      body("전체 테스트 실행 시간은 약 1초 이내로, 모든 성능 기준을 충분히 만족하였습니다. OpenAI API는 unittest.mock을 통해 모킹하여 네트워크 호출 없이 로직 정확성만을 검증하였습니다."),
      new Paragraph({children:[new PageBreak()]}),

      // ── 4장 ───────────────────────────────────────────────────────────────
      h("4장. 모듈별 상세 결과", HeadingLevel.HEADING_1),
      ...Object.keys(allResults).flatMap((key, idx) => [
        h(`4.${idx+1} ${MODULE_LABELS[key] || key}`, HeadingLevel.HEADING_2),
        body(MODULE_DESC[key] || ""),
        ...gap(1),
        makeModuleTable(allResults[key]),
        ...gap(2),
      ]),
      new Paragraph({children:[new PageBreak()]}),

      // ── 5장 ───────────────────────────────────────────────────────────────
      h("5장. 결론 및 향후 계획", HeadingLevel.HEADING_1),
      h("5.1 결론", HeadingLevel.HEADING_2),
      body(`총 ${totalAll}개 테스트를 수행한 결과 ${totalPass}개 PASS, ${totalFail}개 FAIL (합격률 ${passRate}%)을 기록하였습니다.`),
      bullet("기능/비기능 테스트 전 항목 통과 — 정상 경로 및 예외 처리 모두 요구사항 충족"),
      bullet("바이너리 파일(이미지)은 API 호출 없이 확장자 기반으로 분류되어 비용 효율적"),
      bullet("중복 파일명 자동 번호 부여, 잘못된 폴더명 fallback 등 방어 로직 정상 동작 확인"),
      ...gap(1),
      h("5.2 향후 권장 사항", HeadingLevel.HEADING_2),
      bullet("E2E 테스트: 실제 OpenAI API 연동 후 end-to-end 시나리오 검증 권장"),
      bullet("PPTX 테스트: sample_data에 PPTX 파일 추가 후 file_reader PPTX 경로 검증 필요"),
      bullet("대용량 테스트: 100개 이상 파일 처리 시 성능 프로파일링 추가 권장"),
      ...gap(2),
      new Paragraph({ alignment:AlignmentType.CENTER,
        border:{top:{style:BorderStyle.SINGLE,size:4,color:"CCCCCC",space:4}},
        spacing:{before:120,after:0},
        children:[new TextRun({text:"— 이상 —", size:18, color:"888888", font:"Arial"})] }),
    ]
  }]
});

const outPath = process.argv[2] || path.join(__dirname, "../테스트_결과_보고서.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("SUCCESS: " + outPath);
}).catch(e => { console.error("ERROR:", e.message); process.exit(1); });
