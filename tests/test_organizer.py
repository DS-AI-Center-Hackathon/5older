"""기능/비기능 테스트: organizer.py (OpenAI API 모킹)"""
import sys
import json
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.organizer import plan_changes, apply_changes, _deduplicate, _folder_for_binary

SAMPLE = Path(__file__).parent.parent / "sample_data"

PARSED_RULES = {
    "naming_pattern": "YYYYMMDD_주제_출처",
    "folders": ["보고서", "참고자료", "양식", "기타"],
    "notes": "",
}

def make_mock_client(new_name="20260401_테스트_출처.txt", folder="보고서"):
    mock = MagicMock()
    mock.chat.completions.create.return_value.choices[0].message.content = json.dumps({
        "new_name": new_name,
        "target_folder": folder,
    })
    return mock


def run_test(name, fn):
    try:
        start = time.perf_counter()
        result = fn()
        elapsed = (time.perf_counter() - start) * 1000
        return {"name": name, "status": "PASS", "elapsed_ms": round(elapsed, 2), "detail": result}
    except Exception as e:
        return {"name": name, "status": "FAIL", "elapsed_ms": 0, "detail": str(e)}


results = []

# ── 기능 테스트 ────────────────────────────────────────────────────────────────

def test_plan_changes_returns_list():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "test.txt").write_text("내용", encoding="utf-8")
    client = make_mock_client()
    changes = plan_changes(tmp, PARSED_RULES, client)
    assert isinstance(changes, list) and len(changes) == 1
    shutil.rmtree(tmp)
    return f"{len(changes)}개 변경 계획 생성"

def test_plan_changes_fields():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "문서.txt").write_text("보고서 내용", encoding="utf-8")
    client = make_mock_client()
    changes = plan_changes(tmp, PARSED_RULES, client)
    c = changes[0]
    assert all(k in c for k in ["original", "new_name", "target_folder", "status"])
    shutil.rmtree(tmp)
    return "필수 필드(original/new_name/target_folder/status) 모두 존재"

def test_binary_files_no_api_call():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "image.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 10)
    client = make_mock_client()
    changes = plan_changes(tmp, PARSED_RULES, client)
    assert client.chat.completions.create.call_count == 0
    shutil.rmtree(tmp)
    return "이미지 파일: API 호출 없이 확장자 기반 분류"

def test_apply_creates_backup():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "원본.txt").write_text("내용", encoding="utf-8")
    changes = [{"original": "원본.txt", "new_name": "변경.txt", "target_folder": "보고서", "status": "AI 분류"}]
    backup = apply_changes(changes, tmp)
    assert backup.exists() and (backup / "원본.txt").exists()
    shutil.rmtree(tmp)
    return f"백업 폴더 생성 및 원본 보존 확인"

def test_apply_moves_files():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "원본.txt").write_text("내용", encoding="utf-8")
    changes = [{"original": "원본.txt", "new_name": "변경.txt", "target_folder": "보고서", "status": "AI 분류"}]
    apply_changes(changes, tmp)
    assert (tmp / "보고서" / "변경.txt").exists()
    shutil.rmtree(tmp)
    return "파일 이동 및 이름 변경 성공"

def test_deduplicate_unique():
    seen = {}
    name = _deduplicate("파일.txt", seen)
    assert name == "파일.txt"
    return "중복 없을 때 원본 이름 유지"

def test_deduplicate_collision():
    seen = {}
    _deduplicate("파일.txt", seen)
    name2 = _deduplicate("파일.txt", seen)
    assert name2 == "파일_1.txt"
    return "중복 파일명 자동 번호 부여"

def test_invalid_folder_fallback():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "test.txt").write_text("내용", encoding="utf-8")
    client = make_mock_client(folder="존재안하는폴더")
    changes = plan_changes(tmp, PARSED_RULES, client)
    assert changes[0]["target_folder"] == "기타"
    shutil.rmtree(tmp)
    return "잘못된 폴더명 → 기타(catch-all) 폴더로 fallback"

def test_empty_folder():
    tmp = Path(tempfile.mkdtemp())
    client = make_mock_client()
    changes = plan_changes(tmp, PARSED_RULES, client)
    assert changes == []
    shutil.rmtree(tmp)
    return "빈 폴더: 빈 리스트 반환"

def test_performance_10_files():
    tmp = Path(tempfile.mkdtemp())
    for i in range(10):
        (tmp / f"파일{i}.txt").write_text(f"내용 {i}", encoding="utf-8")
    client = make_mock_client()
    start = time.perf_counter()
    plan_changes(tmp, PARSED_RULES, client)
    elapsed = (time.perf_counter() - start) * 1000
    shutil.rmtree(tmp)
    assert elapsed < 5000
    return f"10개 파일 처리 {elapsed:.0f}ms (5초 이내)"

results.append(run_test("plan_changes 리스트 반환", test_plan_changes_returns_list))
results.append(run_test("변경 항목 필수 필드 검증", test_plan_changes_fields))
results.append(run_test("바이너리 파일 API 미호출", test_binary_files_no_api_call))
results.append(run_test("apply_changes 백업 생성", test_apply_creates_backup))
results.append(run_test("apply_changes 파일 이동/이름변경", test_apply_moves_files))
results.append(run_test("중복 없는 파일명 처리", test_deduplicate_unique))
results.append(run_test("중복 파일명 자동 번호 부여", test_deduplicate_collision))
results.append(run_test("잘못된 폴더명 fallback 처리", test_invalid_folder_fallback))
results.append(run_test("빈 폴더 처리", test_empty_folder))
results.append(run_test("10개 파일 처리 성능", test_performance_10_files))

if __name__ == "__main__":
    import json as _json
    print(_json.dumps(results, ensure_ascii=False, indent=2))
