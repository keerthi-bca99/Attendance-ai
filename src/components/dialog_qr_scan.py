import streamlit as st
import time
from src.components.qr_scanner import qr_scanner
from src.pipelines.qr_pipeline import validate_qr_token
from src.database.db import check_qr_attendance_already_marked, create_attendance, sync_attendance_summary
from src.database.config import supabase

# Success Animation with checkmark and canvas-confetti
_SUCCESS_HTML = """
<div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 30px; background: #ffffff; border-radius: 16px; text-align: center; animation: fadeIn 0.5s ease-out;">
  <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52" style="width: 80px; height: 80px; border-radius: 50%; display: block; stroke-width: 4; stroke: #22c55e; stroke-miterlimit: 10; box-shadow: inset 0px 0px 0px #22c55e; animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out 0.9s both;">
    <circle cx="26" cy="26" r="25" fill="none" style="stroke-dasharray: 166; stroke-dashoffset: 166; stroke-width: 4; stroke-miterlimit: 10; stroke: #22c55e; fill: none; animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;"/>
    <path fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8" style="transform-origin: 50% 50%; stroke-dasharray: 48; stroke-dashoffset: 48; stroke-linecap: round; animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;"/>
  </svg>
  <h3 style="color: #22c55e; margin-top: 20px; font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; margin-bottom: 0;">✅ Attendance Confirmed</h3>
</div>

<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
<script>
  if (window.confetti) {
    confetti({
      particleCount: 120,
      spread: 80,
      origin: { y: 0.5 }
    });
  }
</script>

<style>
@keyframes stroke { 100% { stroke-dashoffset: 0; } }
@keyframes scale { 0%, 100% { transform: none; } 50% { transform: scale3d(1.1, 1.1, 1); } }
@keyframes fill { 100% { box-shadow: inset 0px 0px 0px 40px #22c55e; stroke: #fff; } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
"""

# Already Taken Animation with info icon
_ALREADY_TAKEN_HTML = """
<div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 30px; background: #ffffff; border-radius: 16px; text-align: center; animation: fadeIn 0.5s ease-out;">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52" style="width: 80px; height: 80px; border-radius: 50%; display: block; stroke-width: 4; stroke: #3b82f6; stroke-miterlimit: 10; box-shadow: inset 0px 0px 0px #3b82f6; animation: fill_info .4s ease-in-out .4s forwards, scale .3s ease-in-out 0.9s both;">
    <circle cx="26" cy="26" r="25" fill="none" style="stroke-dasharray: 166; stroke-dashoffset: 166; stroke-width: 4; stroke-miterlimit: 10; stroke: #3b82f6; fill: none; animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;"/>
    <path fill="#ffffff" d="M26 12a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zm-2 9h4v18h-4V21z" style="animation: stroke 0.3s 0.8s forwards;"/>
  </svg>
  <h3 style="color: #3b82f6; margin-top: 20px; font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; margin-bottom: 0;">ℹ Attendance Already Recorded</h3>
</div>

<style>
@keyframes stroke { 100% { stroke-dashoffset: 0; } }
@keyframes scale { 0%, 100% { transform: none; } 50% { transform: scale3d(1.1, 1.1, 1); } }
@keyframes fill_info { 100% { box-shadow: inset 0px 0px 0px 40px #3b82f6; stroke: #fff; } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
"""

@st.dialog("Scan QR Code")
def scan_qr_dialog():
    st.markdown("""
        <style>
        div[data-testid="stModal"] {
            padding: 0 !important;
        }
        div[data-testid="stModal"] > div {
            border-radius: 16px !important;
            background: #000000 !important;
            max-width: 100% !important;
            margin: 0 !important;
        }
        div[data-testid="stModalHeader"] {
            display: none !important;
        }
        div[data-testid="stModal"] [data-testid="stVerticalBlock"] {
            padding: 0 !important;
            gap: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if "qr_error" not in st.session_state:
        st.session_state.qr_error = ""
    if "qr_status" not in st.session_state:
        st.session_state.qr_status = "idle"
        
    # Render component with error message and status props
    scanned_val = qr_scanner(
        error_msg=st.session_state.qr_error,
        status=st.session_state.qr_status
    )
    
    if scanned_val:
        # Handle dict or string value returned from component
        if isinstance(scanned_val, dict):
            val = scanned_val.get("value")
        else:
            val = scanned_val

        # Handle navigation / state changes from component
        if val == "BACK":
            st.session_state.qr_error = ""
            st.session_state.qr_status = "idle"
            st.session_state.show_qr_scanner = False
            st.rerun()
            return

        if val == "RESET_STATUS":
            st.session_state.qr_error = ""
            st.session_state.qr_status = "idle"
            st.rerun()
            return

        is_valid, subject_id, session_key, session_timestamp, err = validate_qr_token(val)
        
        if not is_valid:
            st.session_state.qr_error = "Invalid or Expired Code"
            st.session_state.qr_status = "invalid_qr"
            st.rerun()
            return

        student_id = st.session_state.student_data['student_id']
        subject_id = int(subject_id)

        # 1. Validate student eligibility (enrolled in subject?)
        enroll_check = (
            supabase.table('subject_students')
            .select('*')
            .eq('student_id', student_id)
            .eq('subject_id', subject_id)
            .execute()
        )
        if not enroll_check.data:
            st.session_state.qr_error = "Not Enrolled in this Subject"
            st.session_state.qr_status = "error"
            st.rerun()
            return

        # 2. Check if attendance already marked for this class session
        already_marked = check_qr_attendance_already_marked(student_id, subject_id, session_timestamp)
        if already_marked:
            st.session_state.qr_error = "Already Checked In"
            st.session_state.qr_status = "already_recorded"
            st.rerun()
            return

        # 3. Create attendance log
        log_data = [{
            "student_id": student_id,
            "subject_id": subject_id,
            "timestamp": session_timestamp,
            "is_present": True
        }]
        
        try:
            create_attendance(log_data)
            sync_attendance_summary(log_data)

            st.session_state.qr_error = ""
            st.session_state.qr_status = "success"
            st.rerun()

        except Exception as e:
            st.session_state.qr_error = f"System Error: {str(e)}"
            st.session_state.qr_status = "error"
            st.rerun()
