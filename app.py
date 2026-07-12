
import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog

def main():
    st.set_page_config(
        page_title='SnapClass v2.0.0 - Making Attendance faster using AI',
        page_icon= "https://i.ibb.co/YTYGn5qV/logo.png"
    )
    
    # ── Single Active Session Check ──
    if st.session_state.get('is_logged_in'):
        role = st.session_state.get('user_role')
        user_id = None
        if role == 'teacher' and st.session_state.get('teacher_data'):
            user_id = st.session_state.teacher_data.get('teacher_id')
        elif role == 'student' and st.session_state.get('student_data'):
            user_id = st.session_state.student_data.get('student_id')
            
        if role and user_id:
            from src.database.db import verify_user_session
            if not verify_user_session(role, user_id):
                st.session_state.clear()
                st.session_state['login_type'] = None
                st.error("🔒 You have been logged out because this account was logged in on another device.")
                st.toast("Logged out: active session on another device.", icon="⚠️")
                import time
                time.sleep(2)
                st.rerun()

    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()
        
        case None:
            home_screen()


    join_code = st.query_params.get('join-code')
    if join_code:
        if st.session_state.login_type != 'student':
            st.session_state.login_type = 'student'
            st.rerun()
        if st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
            auto_enroll_dialog(join_code)
main()
