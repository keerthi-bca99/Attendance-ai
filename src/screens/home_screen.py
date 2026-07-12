import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.ui.base_layout import style_base_layout, style_background_home
def home_screen():


    header_home()
    style_background_home()
    style_base_layout()


    import os
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    student_img = os.path.join(assets_dir, "student.png")
    teacher_img = os.path.join(assets_dir, "teacher.png")

    import base64
    with open(student_img, "rb") as f:
        student_base64 = base64.b64encode(f.read()).decode()
    with open(teacher_img, "rb") as f:
        teacher_base64 = base64.b64encode(f.read()).decode()

    # Inject large button styles only for portal buttons
    st.markdown("""
        <style>
        /* Larger portal card buttons */
        div[data-testid="stColumn"] button[kind="primary"] {
            padding: 18px 28px !important;
            font-size: 1.15rem !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            min-height: 62px !important;
            letter-spacing: 0.3px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<h2 style="color:#36454F;">I\'m Student</h2>', unsafe_allow_html=True)
        st.markdown(f'<div style="height: 250px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;"><img src="data:image/png;base64,{student_base64}" style="max-height: 100%; max-width: 100%;" /></div>', unsafe_allow_html=True)
        if st.button('Student Portal', type='primary', icon=':material/arrow_outward:', icon_position='right', key='btn_student', use_container_width=True):
            st.session_state['login_type']='student'
            st.rerun()

    with col2:
        st.markdown('<h2 style="color:#36454F;">I\'m Teacher</h2>', unsafe_allow_html=True)
        st.markdown(f'<div style="height: 250px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;"><img src="data:image/png;base64,{teacher_base64}" style="max-height: 100%; max-width: 100%;" /></div>', unsafe_allow_html=True)
        if st.button('Teacher Portal', type='primary', icon=':material/arrow_outward:', icon_position='right', key='btn_teacher', use_container_width=True):
            st.session_state['login_type']='teacher'
            st.rerun()

    footer_home()