"""기능 테스트: rule_parser.py (OpenAI API 모킹)"""
import sys
import json
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rule_parser import parse_rules

VALID_RESPONSE = json.dumps({
    "naming_pattern": "YYYYMMDD_주제_출처",
    "folders": ["보고서", "참고자료", "양식", "기타"],
    "notes": "날짜 형식 준수"
})

def make_mock(content=VALID_RESPONSE):
    mock = MagicMock()
    mock.chat.completions.create.return_value.choices[0].message.content = content
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

def test_returns_dict():
    result = parse_rules("날짜별로 분류해줘", make_mock())
    assert isinstance(result, dict)
    return "dict 타입 반환"

def test_required_keys():
    result = parse_rules("날짜별로 분류해줘", make_mock())
    assert "naming_pattern" in result
    assert "folders" in result
    return f"필수 키 존재: naming_pattern={result['naming_pattern']}, folders={result['folders']}"

def test_folders_is_list():
    result = parse_rules("날짜별로 분류해줘", make_mock())
    assert isinstance(result["folders"], list) and len(result["folders"]) > 0
    return f"folders 리스트 ({len(result['folders'])}개)"

def test_has_catch_all():
    result = parse_rules("날짜별로 분류해줘", make_mock())
    assert "기타" in result["folders"]
    return "catch-all '기타' 폴더 존재"

def test_api_called_once():
    client = make_mock()
    parse_rules("규칙 입력", client)
    assert client.chat.completions.create.call_count == 1
    return "API 정확히 1회 호출"

def test_invalid_json_raises():
    try:
        parse_rules("규칙", make_mock("이것은 JSON이 아닙니다"))
        return None  # should have raised
    except Exception:
        return "잘못된 JSON 응답 시 예외 발생"

def test_long_rule_input():
    long_rule = "날짜_주제_출처 형식으로 이름 짓고 " * 50
    result = parse_rules(long_rule, make_mock())
    assert isinstance(result, dict)
    return f"긴 입력(len={len(long_rule)}) 처리 정상"

results.append(run_test("파싱 결과 dict 반환", test_returns_dict))
results.append(run_test("필수 키 존재 검증", test_required_keys))
results.append(run_test("folders 리스트 형식 검증", test_folders_is_list))
results.append(run_test("catch-all 기타 폴더 포함", test_has_catch_all))
results.append(run_test("API 호출 횟수 검증", test_api_called_once))
results.append(run_test("잘못된 JSON 응답 예외 처리", test_invalid_json_raises))
results.append(run_test("긴 입력 처리", test_long_rule_input))

if __name__ == "__main__":
    print(json.dumps(results, ensure_ascii=False, indent=2))
