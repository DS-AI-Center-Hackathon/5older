import json
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
TESTS_DIR = ROOT / "tests"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="관리자 페이지", page_icon="🛠️", layout="wide")
st.title("🛠️ 관리자 페이지")
st.caption("테스트 실행 및 보고서 관리")

# ── 테스트 실행 ───────────────────────────────────────────────────────────────
st.subheader("🧪 테스트 실행")

col1, col2 = st.columns([2, 1])
with col1:
    run_report = st.checkbox("보고서(DOCX/PDF) 자동 생성", value=True)
run_btn = col2.button("▶ 테스트 실행", type="primary", use_container_width=True)

if run_btn:
    if run_report:
        cmd = [sys.executable, str(TESTS_DIR / "run_report.py")]
        label = "테스트 + 보고서 생성 중..."
    else:
        cmd = [sys.executable, str(TESTS_DIR / "run_all.py")]
        label = "테스트 실행 중..."

    with st.status(label, expanded=True) as status:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        if proc.returncode == 0:
            status.update(label="✅ 완료!", state="complete")
        else:
            status.update(label="❌ 오류 발생", state="error")
            st.error(proc.stderr)
            st.stop()

    # 결과 로드
    result_file = TESTS_DIR / "latest_results.json"
    if result_file.exists():
        data = json.loads(result_file.read_text(encoding="utf-8"))
        st.session_state["last_results"] = data
        st.session_state["show_results"] = True
        st.rerun()

# ── 테스트 결과 표시 ──────────────────────────────────────────────────────────
if st.session_state.get("show_results"):
    data = st.session_state["last_results"]
    all_results = data["results"]
    run_at = data["run_at"]

    st.subheader(f"📊 테스트 결과  `{run_at}`")

    # 요약 지표
    total = pass_cnt = fail_cnt = 0
    for rows in all_results.values():
        for r in rows:
            total += 1
            if r["status"] == "PASS":
                pass_cnt += 1
            else:
                fail_cnt += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체", total)
    c2.metric("PASS ✅", pass_cnt, delta=None)
    c3.metric("FAIL ❌", fail_cnt, delta=None)
    c4.metric("합격률", f"{round(pass_cnt/total*100)}%" if total else "0%")

    st.divider()

    # 모듈별 결과 탭
    MODULE_LABELS = {
        "test_file_reader": "📄 file_reader.py",
        "test_rule_parser": "📐 rule_parser.py",
        "test_organizer":   "📦 organizer.py",
    }
    tabs = st.tabs([MODULE_LABELS.get(k, k) for k in all_results])
    for tab, (key, rows) in zip(tabs, all_results.items()):
        with tab:
            import pandas as pd
            df = pd.DataFrame([
                {
                    "테스트 항목": r["name"],
                    "결과": r["status"],
                    "시간(ms)": r["elapsed_ms"],
                    "상세": r.get("detail", ""),
                }
                for r in rows
            ])

            def color_status(val):
                if val == "PASS":
                    return "color: #00703C; font-weight: bold"
                elif val in ("FAIL", "ERROR"):
                    return "color: #C00000; font-weight: bold"
                return ""

            st.dataframe(
                df.style.map(color_status, subset=["결과"]),
                use_container_width=True,
                hide_index=True,
            )

# ── 보고서 목록 ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📁 저장된 보고서")

reports = sorted(REPORTS_DIR.glob("*.pdf"), reverse=True)

if not reports:
    st.info("아직 생성된 보고서가 없습니다.")
else:
    for pdf in reports:
        docx = pdf.with_suffix(".docx")
        col_name, col_pdf, col_docx = st.columns([4, 1, 1])
        col_name.write(f"📄 {pdf.name}")
        with open(pdf, "rb") as f:
            col_pdf.download_button("PDF", f, file_name=pdf.name,
                                    mime="application/pdf", key=f"pdf_{pdf.name}")
        if docx.exists():
            with open(docx, "rb") as f:
                col_docx.download_button("DOCX", f, file_name=docx.name,
                                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                         key=f"docx_{docx.name}")
