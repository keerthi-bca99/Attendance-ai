import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.database.db import get_all_students, create_student, get_student_subjects, get_attendance_summary, get_student_attendance, unenroll_student_to_subject
import time

from src.components.dialog_enroll import enroll_dialog
from src.components.dialog_qr_scan import scan_qr_dialog
from src.components.subject_card import subject_card

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.markdown(f'<h3 style="color:#36454F; font-family:Outfit,sans-serif; margin:0;">Welcome, {student_data["name"]}</h3>', unsafe_allow_html=True)
        if st.button("Logout", type='secondary', key='loginbackbtn'):
            st.session_state['is_logged_in'] = False
            del st.session_state.student_data 
            st.rerun()


    st.space()

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown('<h2 style="color:#36454F;">Your Enrolled Subjects</h2>', unsafe_allow_html=True)
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()
    with c3:
        if st.button('Scan QR Code', type='secondary', width='stretch'):
            st.session_state.qr_error = ""
            st.session_state.qr_status = "idle"
            st.session_state.show_qr_scanner = True
            st.rerun()

    if st.session_state.get('show_qr_scanner', False):
        scan_qr_dialog()


    st.divider()


    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        summary_rows = get_attendance_summary(student_id)
        logs = get_student_attendance(student_id)

    # present_count from attendance_summary (fast, pre-aggregated)
    present_map = {row['subject_id']: row['present_count'] for row in summary_rows}

    # total count per subject from attendance_logs
    total_map = {}
    for log in logs:
        sid = log['subject_id']
        total_map[sid] = total_map.get(sid, 0) + 1


    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']


        attended = present_map.get(sid, 0)
        total    = total_map.get(sid, 0)
        def unenroll_button(s=sub, s_id=sid):
                if st.button(f"Unenroll from {s['name']}", key=f"unenroll_{s_id}", type='tertiary', width='stretch', icon=':material/delete_forever:'):
                    unenroll_student_to_subject(student_id, s_id)
                    st.toast(f"Unenrolled from {s['name']} successfully!")
                    st.rerun()

        with cols[i % 2]:

            subject_card(
                name = sub['name'],
                code =sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📅', 'Total', total),
                    ('✅', 'Attended', attended),
                ],
                footer_callback=unenroll_button
            )
    footer_dashboard()


def student_screen():


    style_background_dashboard()
    style_base_layout()


    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.markdown('<h2 style="color:#36454F; text-align:center;">Login with FaceID</h2>', unsafe_allow_html=True)
    st.space()
    st.space()
    
    show_registration = False
    st.markdown("""
        <style>
            div[data-testid="stCameraInput"] label p {
                color: #6082B6 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        img = np.array(Image.open(photo_source))

        with st.spinner('AI is scanning..'):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning('Face not found!')
            elif num_faces >1:
                st.warning('Multiple faces found')
            else:
                if detected:
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()
                    student = next((s for s in all_students if s['student_id']==student_id), None)

                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        from src.database.db import register_user_session
                        register_user_session('student', student['student_id'])
                        st.toast(f"Welcome Back {student['name']}")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info('Face not recognized! You might be a new student!')
                    show_registration = True
    if show_registration:
        st.markdown("""
            <style>
                div[data-testid="stTextInput"] label p {
                    color: #36454F !important;
                }
            </style>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<h2 style="color:#36454F;">Register new Profile</h2>', unsafe_allow_html=True)
            new_name = st.text_input("Enter your name", placeholder='E.g. Hamza Rizvi')

            st.info("Ensure your face is clearly visible to the camera for registration.")

            if st.button('Create Account', type='primary'):
                if new_name:
                    with st.spinner('Creating profile..'):
                        img = np.array(Image.open(photo_source))
                        encodings= get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            response_data = create_student(new_name, face_embedding=face_emb)

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                from src.database.db import register_user_session
                                register_user_session('student', response_data[0]['student_id'])
                                st.toast(f'Profile Created! Hi {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error('Couldnt capture your facial features for registration')

                else:
                    st.warning('Please enter your name!')


        
    footer_dashboard()