"""기능 테스트: file_reader.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_reader import extract_text

SAMPLE = Path(__file__).parent.parent / "sample_data"


def run_test(name, fn):
    try:
        start = time.perf_counter()
        result = fn()
        elapsed = (time.perf_counter() - start) * 1000
        status = "PASS" if result else "FAIL"
        return {"name": name, "status": status, "elapsed_ms": round(elapsed, 2), "detail": result}
    except Exception as e:
        return {"name": name, "status": "ERROR", "elapsed_ms": 0, "detail": str(e)}


results = []

# ── 기능 테스트 ────────────────────────────────────────────────────────────────

def test_txt():
    text = extract_text(SAMPLE / "문서1.txt")
    assert text and "영업" in text
    return f"추출 성공 ({len(text)}자)"

def test_docx():
    text = extract_text(SAMPLE / "보고서초안v2.docx")
    assert text and len(text) > 10
    return f"추출 성공 ({len(text)}자)"

def test_xlsx():
    text = extract_text(SAMPLE / "Book1.xlsx")
    assert text and len(text) > 10
    return f"추출 성공 ({len(text)}자)"

def test_unsupported_ext():
    text = extract_text(SAMPLE / "스크린샷 2026-04-10 143022.png")
    assert text is None
    return "None 반환 (정상)"

def test_nonexistent_file():
    text = extract_text(SAMPLE / "없는파일.txt")
    assert text is None
    return "None 반환 (정상)"

def test_txt_max_chars():
    text = extract_text(SAMPLE / "문서1.txt")
    assert text is not None and len(text) <= 500
    return f"최대 500자 제한 준수 ({len(text)}자)"

def test_multiple_files_performance():
    files = list(SAMPLE.iterdir())
    start = time.perf_counter()
    for f in files:
        extract_text(f)
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 3000, f"처리 시간 초과: {elapsed:.0f}ms"
    return f"{len(files)}개 파일 처리 {elapsed:.0f}ms"

def test_korean_encoding():
    text = extract_text(SAMPLE / "회의록_최종.txt")
    assert text and "미팅" in text
    return "한글 인코딩 정상"

def test_empty_content_file(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    text = extract_text(empty)
    assert text == "" or text is None
    return "빈 파일 처리 정상"

def test_special_chars_filename(tmp_path):
    f = tmp_path / "Copy of 양식 (1).txt"
    f.write_text("테스트 내용", encoding="utf-8")
    text = extract_text(f)
    assert text is not None
    return "특수문자 파일명 처리 정상"

import tempfile, pathlib
tmp = pathlib.Path(tempfile.mkdtemp())

results.append(run_test("TXT 파일 텍스트 추출", test_txt))
results.append(run_test("DOCX 파일 텍스트 추출", test_docx))
results.append(run_test("XLSX 파일 텍스트 추출", test_xlsx))
results.append(run_test("미지원 확장자(.png) 처리", test_unsupported_ext))
results.append(run_test("존재하지 않는 파일 처리", test_nonexistent_file))
results.append(run_test("최대 글자 수(500자) 제한", test_txt_max_chars))
results.append(run_test("다중 파일 처리 성능(3초 이내)", test_multiple_files_performance))
results.append(run_test("한글 인코딩 처리", test_korean_encoding))
results.append(run_test("빈 파일 처리", lambda: test_empty_content_file(tmp)))
results.append(run_test("특수문자 포함 파일명 처리", lambda: test_special_chars_filename(tmp)))

if __name__ == "__main__":
    import json
    print(json.dumps(results, ensure_ascii=False, indent=2))
