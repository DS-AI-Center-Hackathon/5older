import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from core.organizer import apply_changes, plan_changes
from core.rule_parser import parse_rules


def _pick_folder() -> str:
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    folder = filedialog.askdirectory(title="정리할 폴더 선택")
    root.destroy()
    return folder

load_dotenv()

st.set_page_config(page_title="Clean Folder", page_icon="🗂️", layout="centered")
st.title("🗂️ Clean Folder")
st.caption("AI가 파일 내용을 읽고 규칙에 따라 자동으로 이름 변경 + 폴더 분류합니다.")

# ── 입력 ──────────────────────────────────────────────────────────────────────
st.markdown("정리할 폴더 경로")
_col_path, _col_btn = st.columns([5, 1], vertical_alignment="bottom")
with _col_path:
    folder_input = st.text_input(
        "정리할 폴더 경로",
        placeholder="예: C:/Users/User/Downloads",
        key="folder_input",
        label_visibility="collapsed",
    )
with _col_btn:
    if st.button("📂 선택", use_container_width=True, help="파일 탐색기로 폴더 선택"):
        picked = _pick_folder()
        if picked:
            st.session_state["folder_input"] = picked
        st.rerun()

default_rule = "날짜_주제_출처 형식으로 이름 짓고, 보고서 / 참고자료 / 양식 / 기타 폴더로 분류해줘"
rule_input = st.text_area(
    "정리 규칙 (자연어)",
    value=default_rule,
    height=100,
)

api_key = st.text_input(
    "OpenAI API Key",
    value=os.getenv("OPENAI_API_KEY", ""),
    type="password",
    help=".env 파일에 OPENAI_API_KEY를 설정하면 자동으로 불러옵니다.",
)

analyze_btn = st.button("🔍 분석 시작", type="primary", use_container_width=True)

# ── 분석 ──────────────────────────────────────────────────────────────────────
if analyze_btn:
    folder_path = Path(folder_input.strip())
    if not folder_path.exists() or not folder_path.is_dir():
        st.error("유효한 폴더 경로를 입력해주세요.")
        st.stop()
    if not api_key.strip():
        st.error("Anthropic API Key를 입력해주세요.")
        st.stop()
    if not rule_input.strip():
        st.error("정리 규칙을 입력해주세요.")
        st.stop()

    client = OpenAI(api_key=api_key.strip())

    # Pass 1: 규칙 파싱
    with st.status("규칙을 파싱하는 중...", expanded=False):
        try:
            parsed_rules = parse_rules(rule_input, client)
            st.write(f"**명명 패턴:** {parsed_rules.get('naming_pattern', '-')}")
            st.write(f"**폴더 목록:** {', '.join(parsed_rules['folders'])}")
        except Exception as e:
            st.error(f"규칙 파싱 실패: {e}")
            st.stop()

    # Pass 2: 파일 분류
    progress_bar = st.progress(0, text="파일 분석 준비 중...")
    status_text = st.empty()

    def on_progress(i, total, filename):
        pct = int((i / total) * 100) if total else 0
        progress_bar.progress(pct, text=f"분석 중... ({i}/{total})")
        status_text.caption(f"처리 중: `{filename}`")

    try:
        changes = plan_changes(folder_path, parsed_rules, client, progress_callback=on_progress)
        progress_bar.progress(100, text="분석 완료!")
        status_text.empty()
    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
        st.stop()

    st.session_state["changes"] = changes
    st.session_state["folder_path"] = folder_path
    st.session_state["analyzed"] = True

# ── Preview ───────────────────────────────────────────────────────────────────
if st.session_state.get("analyzed"):
    changes = st.session_state["changes"]
    folder_path = st.session_state["folder_path"]

    st.subheader("📋 변경 Preview")

    import pandas as pd
    df = pd.DataFrame([
        {
            "원본 파일명": c["original"],
            "새 파일명": c["new_name"],
            "이동할 폴더": c["target_folder"],
            "처리 방식": c["status"],
        }
        for c in changes
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    apply_btn = col1.button("✅ 적용", type="primary", use_container_width=True)
    cancel_btn = col2.button("❌ 취소", use_container_width=True)

    if cancel_btn:
        for key in ["changes", "folder_path", "analyzed"]:
            st.session_state.pop(key, None)
        st.rerun()

    if apply_btn:
        with st.spinner("파일을 이동하는 중..."):
            try:
                backup_dir = apply_changes(changes, folder_path)
                st.success(f"✅ 완료! 원본 백업: `{backup_dir}`")
            except Exception as e:
                st.error(f"적용 중 오류: {e}")
                st.stop()

        # 결과 요약
        st.subheader("📊 결과 요약")
        folder_counts: dict[str, int] = {}
        for c in changes:
            folder_counts[c["target_folder"]] = folder_counts.get(c["target_folder"], 0) + 1

        cols = st.columns(len(folder_counts))
        for col, (folder, count) in zip(cols, folder_counts.items()):
            col.metric(folder, f"{count}개")

        st.caption(f"총 {len(changes)}개 파일 처리 완료")

        for key in ["changes", "folder_path", "analyzed"]:
            st.session_state.pop(key, None)
