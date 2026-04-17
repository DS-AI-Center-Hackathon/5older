"""테스트 실행 → DOCX 보고서 생성 → PDF 변환 원스텝 스크립트"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TESTS_DIR = Path(__file__).parent
ROOT = TESTS_DIR.parent
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
DOCX = REPORTS_DIR / f"테스트_결과_보고서_{timestamp}.docx"
PDF  = REPORTS_DIR / f"테스트_결과_보고서_{timestamp}.pdf"

def run(label, cmd, **kwargs):
    print(f"\n{'='*50}\n{label}\n{'='*50}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"[오류] {label} 실패")
        sys.exit(result.returncode)

print(f"\n[Clean Folder 테스트 보고서 생성] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. 테스트 실행 → latest_results.json 저장
run("1단계: 테스트 실행", [sys.executable, str(TESTS_DIR / "run_all.py")])

# 2. DOCX 보고서 생성
run("2단계: DOCX 보고서 생성",
    ["node", str(TESTS_DIR / "make_report.js"), str(DOCX)])

# 3. PDF 변환
run("3단계: PDF 변환", [sys.executable, "-c",
    f"from docx2pdf import convert; convert(r'{DOCX}', r'{PDF}'); print('PDF 저장 완료')"
])

print(f"\n완료!")
print(f"  DOCX: {DOCX}")
print(f"  PDF : {PDF}")
