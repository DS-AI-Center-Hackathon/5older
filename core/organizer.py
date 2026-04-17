import json
import shutil
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from .file_reader import extract_text

CLASSIFY_SYSTEM = """You are a file classification assistant.
Given a file's name, extension, and a short excerpt of its content, plus a set of organization rules,
decide the best new filename and which folder it belongs to.

Output ONLY a JSON object:
{
  "new_name": "<new filename with extension>",
  "target_folder": "<folder name from the provided list>"
}

Rules for new_name:
- Follow the naming_pattern from the rules exactly.
- Keep the original file extension.
- Use only safe filename characters (no /, \\, :, *, ?, ", <, >, |).
- If the content is too short or unreadable, derive name from the original filename.

Rules for target_folder:
- Must be one of the folder names provided.
- Use the catch-all folder if nothing fits.

Output only valid JSON, no markdown."""

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"}
BINARY_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | {".zip", ".exe", ".dmg", ".iso"}


def plan_changes(
    folder_path: Path,
    parsed_rules: dict,
    client: OpenAI,
    progress_callback=None,
) -> list[dict]:
    files = [f for f in folder_path.iterdir() if f.is_file() and not f.name.startswith("_backup")]
    results = []
    seen_names: dict[str, int] = {}

    for i, file in enumerate(files):
        if progress_callback:
            progress_callback(i, len(files), file.name)

        ext = file.suffix.lower()
        if ext in BINARY_EXTENSIONS:
            folder = _folder_for_binary(ext, parsed_rules["folders"])
            new_name = _deduplicate(file.name, seen_names)
            results.append({
                "original": file.name,
                "new_name": new_name,
                "target_folder": folder,
                "status": "확장자 기반",
            })
            continue

        text = extract_text(file)
        if text is None:
            new_name = _deduplicate(file.name, seen_names)
            results.append({
                "original": file.name,
                "new_name": new_name,
                "target_folder": parsed_rules["folders"][-1],
                "status": "분석 불가",
            })
            continue

        try:
            decision = _classify_file(file.name, text or "", parsed_rules, client)
            new_name = _deduplicate(decision["new_name"], seen_names)
            target = decision["target_folder"]
            if target not in parsed_rules["folders"]:
                target = parsed_rules["folders"][-1]
            results.append({
                "original": file.name,
                "new_name": new_name,
                "target_folder": target,
                "status": "AI 분류",
            })
        except Exception as e:
            new_name = _deduplicate(file.name, seen_names)
            results.append({
                "original": file.name,
                "new_name": new_name,
                "target_folder": parsed_rules["folders"][-1],
                "status": f"오류: {e}",
            })

    return results


def apply_changes(changes: list[dict], folder_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = folder_path / f"_backup_{timestamp}"
    backup_dir.mkdir()

    for item in changes:
        src = folder_path / item["original"]
        if not src.exists():
            continue
        shutil.copy2(src, backup_dir / item["original"])

    for item in changes:
        src = folder_path / item["original"]
        if not src.exists():
            continue
        target_dir = folder_path / item["target_folder"]
        target_dir.mkdir(exist_ok=True)
        dst = target_dir / item["new_name"]
        src.rename(dst)

    return backup_dir


def _classify_file(filename: str, text: str, parsed_rules: dict, client: OpenAI) -> dict:
    user_msg = (
        f"File name: {filename}\n"
        f"Content excerpt:\n{text}\n\n"
        f"Naming pattern: {parsed_rules.get('naming_pattern', '')}\n"
        f"Available folders: {parsed_rules['folders']}\n"
        f"Extra notes: {parsed_rules.get('notes', '')}"
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=256,
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    return json.loads(response.choices[0].message.content.strip())


def _folder_for_binary(ext: str, folders: list[str]) -> str:
    if ext in IMAGE_EXTENSIONS:
        for f in folders:
            if any(k in f for k in ["이미지", "사진", "image", "photo"]):
                return f
    if ext in VIDEO_EXTENSIONS:
        for f in folders:
            if any(k in f for k in ["동영상", "video"]):
                return f
    return folders[-1]


def _deduplicate(name: str, seen: dict[str, int]) -> str:
    if name not in seen:
        seen[name] = 0
        return name
    seen[name] += 1
    p = Path(name)
    return f"{p.stem}_{seen[name]}{p.suffix}"
