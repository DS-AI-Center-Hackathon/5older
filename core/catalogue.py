import json
from pathlib import Path

CATALOGUE_PATH = Path(__file__).parent.parent / "rules_catalogue.json"

DEFAULT_ENTRIES = [
    {
        "name": "날짜_주제_출처 기본 분류",
        "rule": "날짜_주제_출처 형식으로 이름 짓고, 보고서 / 참고자료 / 양식 / 기타 폴더로 분류해줘",
    },
    {
        "name": "프로젝트 문서 정리",
        "rule": "프로젝트명_날짜 형식으로 이름 짓고, 기획 / 개발 / 디자인 / 기타 폴더로 분류해줘",
    },
    {
        "name": "사진 및 미디어 정리",
        "rule": "YYYYMMDD_설명 형식으로 이름 짓고, 사진 / 동영상 / 기타 폴더로 분류해줘",
    },
]


def load() -> list[dict]:
    if not CATALOGUE_PATH.exists():
        save(DEFAULT_ENTRIES)
        return DEFAULT_ENTRIES.copy()
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save(entries: list[dict]) -> None:
    with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def upsert(entries: list[dict], name: str, rule: str) -> list[dict]:
    for entry in entries:
        if entry["name"] == name:
            entry["rule"] = rule
            save(entries)
            return entries
    entries.append({"name": name, "rule": rule})
    save(entries)
    return entries


def delete(entries: list[dict], name: str) -> list[dict]:
    entries = [e for e in entries if e["name"] != name]
    save(entries)
    return entries
