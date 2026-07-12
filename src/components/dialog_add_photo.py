import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
from PIL import Image
import time


@st.dialog("Capture or upload photos")
def add_photos_dialog():

    st.write('Add classroom photos to scan for attendance')

    tab1, tab2 = st.tabs(["Camera", "Upload photos"])

    with tab1:
        cam_photo = st.camera_input('Take Snapshot', key='dialog_cam')
        if cam_photo:
            st.session_state.attendance_images.append(Image.open(cam_photo))
            st.toast('Photo Captured')
            st.rerun()

    with tab2:
        st.file_uploader('choose image files', type=['jpg', 'png', 'jpeg'], accept_multiple_files=True, key='dialog_upload')

    st.divider()
    if st.button('Done', type='primary', width='stretch'):
        uploaded_files = st.session_state.get('dialog_upload')
        if uploaded_files:
            for f in uploaded_files:
                st.session_state.attendance_images.append(Image.open(f))
            st.toast('Photo(s) Uploaded Successfully')
        st.rerun()
