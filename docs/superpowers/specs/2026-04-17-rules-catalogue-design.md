# Rules Catalogue Feature — Design Spec
**Date:** 2026-04-17

## Summary

Add a persistent `rules_catalogue.json` to the project root so users can save, select, and manage named rule presets from the Streamlit UI. Every edit syncs immediately to disk.

---

## Data Structure

`rules_catalogue.json` lives at the project root (sibling of `app.py`). Format:

```json
[
  {
    "name": "날짜_주제_출처 기본 분류",
    "rule": "날짜_주제_출처 형식으로 이름 짓고, 보고서 / 참고자료 / 양식 / 기타 폴더로 분류해줘"
  },
  {
    "name": "프로젝트 문서 정리",
    "rule": "프로젝트명_날짜 형식으로 이름 짓고, 기획 / 개발 / 디자인 / 기타 폴더로 분류해줘"
  },
  {
    "name": "사진 및 미디어 정리",
    "rule": "YYYYMMDD_설명 형식으로 이름 짓고, 사진 / 동영상 / 기타 폴더로 분류해줘"
  }
]
```

- If the file does not exist, it is auto-created with the 3 defaults above.
- Each entry: `name` (unique display label) + `rule` (natural language text passed to `parse_rules`).

---

## New Module: `core/catalogue.py`

Four pure functions. File path is a module-level constant resolved relative to `__file__` so it always points to the project root regardless of the working directory.

| Function | Signature | Behavior |
|----------|-----------|----------|
| `load()` | `() -> list[dict]` | Read JSON; auto-create with defaults if missing |
| `save(entries)` | `(list[dict]) -> None` | Overwrite JSON with full list |
| `upsert(entries, name, rule)` | `(list, str, str) -> list` | Update existing entry or append new one; calls `save` |
| `delete(entries, name)` | `(list, str) -> list` | Remove entry by name; calls `save` |

---

## UI Changes (`app.py`)

The catalogue block is inserted **above** the existing `rule_input` text_area.

### Layout

```
┌─────────────────────────────────────────────────────┐
│ 규칙 카탈로그                                        │
│ [selectbox: "직접 입력" | 규칙1 | 규칙2 ...]         │
│ caption: 📁 .../rules_catalogue.json                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 정리 규칙 (자연어)                                   │
│ [text_area — auto-filled on selection]               │
└─────────────────────────────────────────────────────┘

Row 1 (save-in-place):
┌──────────────────────────────────────┐
│ [💾 저장] — disabled if "직접 입력"  │
└──────────────────────────────────────┘

Row 2 (save-as-new):
┌─────────────────────────────────┬────────────────────────┐
│ [text_input: 새 규칙 이름 입력] │ [📋 다른 이름으로 저장] │
│                                 │  disabled if name empty │
└─────────────────────────────────┴────────────────────────┘

Row 3 (delete):
┌───────────────────────────────────────┐
│ [🗑️ 삭제] — disabled if "직접 입력"  │
└───────────────────────────────────────┘
```

### Interaction Rules

| Action | Condition | Result |
|--------|-----------|--------|
| selectbox 변경 | 항목 선택 | text_area에 해당 rule 자동 입력 |
| selectbox 변경 | "직접 입력" | text_area 비워짐 |
| 💾 저장 | 항목 선택됨 | 현재 text_area 내용으로 해당 항목 rule 업데이트 → JSON 즉시 저장 → `st.rerun()` |
| 📋 다른 이름으로 저장 | 새 이름 입력됨 | 새 항목 추가 (또는 동일 이름이면 덮어쓰기) → JSON 즉시 저장 → `st.rerun()` |
| 🗑️ 삭제 | 항목 선택됨 | 해당 항목 제거 → JSON 즉시 저장 → `st.rerun()` |

- 파일 경로를 selectbox 하단 caption으로 항상 표시 (회사원이 파일 위치를 알 수 있도록).
- `st.session_state`로 selectbox 선택값을 유지해 `st.rerun()` 후에도 선택 상태 복원.

---

## Files Changed

| File | Change |
|------|--------|
| `core/catalogue.py` | **New** — catalogue CRUD module |
| `rules_catalogue.json` | **New** — auto-created at runtime if absent |
| `app.py` | **Modified** — add catalogue UI block above rule_input |

No changes to `core/rule_parser.py`, `core/organizer.py`, or `core/file_reader.py`.
