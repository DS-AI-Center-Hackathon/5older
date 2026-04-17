"""모든 테스트 실행 후 JSON 결과 출력 및 저장"""
import json
import importlib.util
from datetime import datetime
from pathlib import Path

TESTS = [
    "test_file_reader",
    "test_rule_parser",
    "test_organizer",
]

all_results = {}

for module_name in TESTS:
    spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).parent / f"{module_name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    all_results[module_name] = mod.results

output = {
    "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "results": all_results,
}

out_path = Path(__file__).parent / "latest_results.json"
out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(output, ensure_ascii=False, indent=2))
