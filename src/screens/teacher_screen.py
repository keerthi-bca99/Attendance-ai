import streamlit as st
import time

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
import numpy as np

from datetime import datetime

import pandas as pd

from src.database.config import supabase

def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type=="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()





def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.markdown(f'<h3 style="color:#36454F; font-family:Outfit,sans-serif; margin:0;">Welcome, {teacher_data["name"]}</h3>', unsafe_allow_html=True)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data 
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'
    tab1, tab2, tab3, tab4 = st.columns(4)


    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance',type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records',type=type3, width='stretch', icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()

    with tab4:
        type4 = "primary" if st.session_state.current_teacher_tab == 'qr_attendance' else "tertiary"
        if st.button('QR Attendance', type=type4, width='stretch', icon=':material/qr_code:'):
            st.session_state.current_teacher_tab = 'qr_attendance'
            st.rerun()


    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()
    if st.session_state.current_teacher_tab == "qr_attendance":
        teacher_tab_qr_attendance()

    


    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.markdown('<h2 style="color:#36454F;">Take AI Attendance</h2>', unsafe_allow_html=True)


    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('You havent created any subjects yet! Please create one to begin!')
        return
    
    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3,1], vertical_alignment='bottom')

    st.markdown("""
        <style>
            div[data-testid="stSelectbox"] label p {
                color: #36454F !important;
            }
        </style>
    """, unsafe_allow_html=True)
    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))

    with col2:
        if st.button('Add Photos', type='primary', icon=':material/photo_prints:', width='stretch'):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    if st.session_state.attendance_images:
        st.markdown('<h2 style="color:#36454F;">Added Photos</h2>', unsafe_allow_html=True)
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4 ]:
                st.image(img, width='stretch', caption=f'Photo {idx+1}')
    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button('Clear all photos', width='stretch', type='tertiary', icon=':material/delete:', disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()


    with c2:
        
        if st.button('Run Face Analysis', width='stretch', type='secondary', icon=':material/analytics:', disabled=not has_photos):
            with st.spinner('Deep scanning classroom photos...'):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendance(img_np)


                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)

                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")

                enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id',selected_subject_id ).execute()
                enrolled_students = enrolled_res.data

                if not enrolled_students:
                    st.warning('No students enrolled in this course')
                else:

                    results, attendance_to_log  = [], []

                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


                    for node in enrolled_students:
                        student = node['students']
                        sources = all_detected_ids.get(int(student['student_id']), [])
                        is_present= len(sources) > 0

                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })

                        attendance_to_log.append({
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present)
                        })

                attendance_result_dialog(pd.DataFrame(results), attendance_to_log)













def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h2 style="color:#36454F;">Manage Subjects</h2>', unsafe_allow_html=True)

    with col2:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)


    # LIST all SUBJECTS
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("🫂", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]
            def share_btn(s=sub):
                if st.button(f"Share Code: {s['name']}", key=f"share_{s['subject_code']}", icon=":material/share:"):
                    share_subject_dialog(s['name'], s['subject_code'])
                st.space()

            subject_card(
                name = sub['name'],
                code = sub['subject_code'],
                section = sub['section'],
                stats=stats,
                footer_callback=share_btn
            )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def df_to_custom_html(df):
    if df.empty:
        return "<p style='color: #64748b; text-align: center; padding: 20px;'>No columns selected to display.</p>"
        
    is_fs = st.session_state.get('full_screen_records', False)
    container_class = "custom-table-container fullscreen-table" if is_fs else "custom-table-container"
    html = f'<div class="{container_class}">'
    html += '<table class="custom-table">'
    
    # Headers
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead>'
    
    # Rows
    html += '<tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            if col == "Status":
                status_class = "status-present" if val == "Present" else "status-absent"
                status_icon = "✅ Present" if val == "Present" else "❌ Absent"
                html += f'<td class="{status_class}">{status_icon}</td>'
            else:
                html += f'<td>{val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html

def render_records_table_view():
    teacher_id = st.session_state.teacher_data['teacher_id']
    records = get_attendance_for_teacher(teacher_id)

    if not records:
        st.info("No attendance records yet. Run a session to get started.")
        return
    
    data = []
    for r in records:
        ts = r.get('timestamp')
        sub = r.get('subjects', {})
        student = r.get('students', {})
        teacher_name = sub.get('teachers', {}).get('name', 'N/A') if sub.get('teachers') else 'N/A'
        
        data.append({
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": sub.get('name', 'N/A'),
            "Subject Code": sub.get('subject_code', 'N/A'),
            "Student Name": student.get('name', 'N/A'),
            "Student ID": str(student.get('student_id', 'N/A')),
            "Teacher": teacher_name,
            "Status": "Present" if r.get('is_present') else "Absent"
        })

    df = pd.DataFrame(data)

    if st.session_state.get('full_screen_records', False):
        st.markdown("""
            <style>
            .st-key-exit_fs_float button {
                position: fixed !important;
                top: 10px !important;
                right: 20px !important;
                z-index: 1000001 !important;
                background-color: #ef4444 !important;
                color: white !important;
                border-radius: 30px !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
                padding: 6px 20px !important;
                font-family: Outfit, sans-serif !important;
            }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("""
            <div style="position: fixed; top: 0; left: 0; right: 0; height: 60px; background: #36454F; z-index: 1000000; display: flex; align-items: center; padding-left: 20px;">
                <span style="color: white; font-family: Outfit, sans-serif; font-weight: 600; font-size: 1.1rem;">Full Screen Attendance Records</span>
            </div>
        """, unsafe_allow_html=True)
        with st.container(key="exit_fs_float"):
            if st.button("Exit Full Screen", key="btn_exit_fs_float"):
                st.session_state.full_screen_records = False
                st.rerun()

    # Styling injection
    st.markdown("""
        <style>
        .st-key-attendance_toolbar button, 
        .st-key-attendance_toolbar div[data-testid="stPopover"] button {
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            max-width: 38px !important;
            padding: 0 !important;
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #ffffff !important;
            color: #2563eb !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }

        .st-key-attendance_toolbar button:hover,
        .st-key-attendance_toolbar div[data-testid="stPopover"] button:hover {
            background-color: #eff6ff !important;
            border-color: #bfdbfe !important;
            color: #1d4ed8 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.08), 0 2px 4px -1px rgba(37, 99, 235, 0.04) !important;
        }

        .st-key-attendance_toolbar button:active,
        .st-key-attendance_toolbar div[data-testid="stPopover"] button:active {
            background-color: #dbeafe !important;
            transform: translateY(0) !important;
        }

        .st-key-attendance_toolbar button span,
        .st-key-attendance_toolbar div[data-testid="stPopover"] button span {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        .st-key-attendance_toolbar > div {
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-end !important;
            align-items: center !important;
            gap: 8px !important;
        }
        .st-key-attendance_toolbar [data-testid="column"] {
            width: auto !important;
            flex: none !important;
        }

        div[data-testid="stTextInput"] input {
            height: 38px !important;
            font-size: 0.875rem !important;
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
        }

        /* Solid black popover card with rounded corners and no border */
        div[data-baseweb="popover"] {
            border: none !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4) !important;
            background: transparent !important;
        }
        div[data-testid="stPopoverBody"] {
            background-color: #000000 !important;
            color: #ffffff !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            min-width: 220px !important;
            border: none !important;
        }
        /* Style Streamlit checkbox inside popover */
        div[data-testid="stPopoverBody"] label p {
            color: #ffffff !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
        }
        /* Style checkbox inputs */
        div[data-testid="stPopoverBody"] input[type="checkbox"] {
            accent-color: #EB459E !important;
        }

        .custom-table-container {
            max-height: 480px;
            overflow-y: auto;
            overflow-x: auto;
            width: 100% !important;
            max-width: 100% !important;
            display: block !important;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            background: #ffffff;
            margin-top: 16px;
            -webkit-overflow-scrolling: touch;
        }
        .custom-table-container.fullscreen-table {
            position: fixed !important;
            top: 60px !important;
            left: 0 !important;
            width: 100vw !important;
            height: calc(100vh - 60px) !important;
            max-height: calc(100vh - 60px) !important;
            max-width: 100vw !important;
            z-index: 999999 !important;
            margin: 0 !important;
            border-radius: 0 !important;
            background: #ffffff !important;
        }
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: clamp(0.75rem, 2.5vw, 0.875rem);
            text-align: left;
        }
        .custom-table th {
            position: sticky;
            top: 0;
            background: #36454F;
            color: #ffffff;
            font-weight: 600;
            padding: 14px 18px;
            border-bottom: 1.5px solid #2d3748;
            z-index: 10;
        }
        .custom-table td {
            padding: 12px 18px;
            color: #334155;
            border-bottom: 1px solid #e2e8f0;
        }
        .custom-table tbody tr:nth-child(even) {
            background-color: #f8fafc !important;
        }
        .custom-table tbody tr:nth-child(odd) {
            background-color: #ffffff !important;
        }
        .custom-table tbody tr:hover {
            background-color: #f1f5f9 !important;
        }
        .status-present {
            color: #16a34a !important;
            font-weight: 600;
        }
        .status-absent {
            color: #dc2626 !important;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize column visibility session state
    all_cols = ["Time", "Subject", "Subject Code", "Student Name", "Student ID", "Teacher", "Status"]
    if "cols_select" not in st.session_state:
        st.session_state.cols_select = all_cols

    selected_cols = st.session_state.get("cols_select", all_cols)

    # 1. Global Search input
    col_search, col_toolbar = st.columns([3, 2], vertical_alignment="bottom")
    
    with col_search:
        search_query = st.text_input("🔍 Search records", placeholder="Type to search...", label_visibility="collapsed")

    # Filter dataframe based on search
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    # Filter columns
    if not selected_cols:
        display_df = pd.DataFrame()
    else:
        display_df = filtered_df[selected_cols]

    # Generate CSV data
    csv_data = display_df.to_csv(index=False).encode('utf-8')

    # First time user tooltip check
    is_first_time = not st.session_state.get('visited_records_before', False)
    if is_first_time:
        st.session_state.visited_records_before = True
        st.markdown("""
            <style>
            @keyframes fadeOutLabels {
                0% { opacity: 1; max-height: 20px; margin-top: 4px; visibility: visible; }
                80% { opacity: 1; max-height: 20px; margin-top: 4px; }
                100% { opacity: 0; max-height: 0px; margin-top: 0px; visibility: hidden; overflow: hidden; display: none; }
            }
            .first-time-label {
                animation: fadeOutLabels 2.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                font-size: 0.72rem !important;
                color: #475569 !important;
                text-align: center;
                font-weight: 500;
                white-space: nowrap;
            }
            </style>
        """, unsafe_allow_html=True)

    # 2. Render Compact Action Toolbar
    with col_toolbar:
        with st.container(key="attendance_toolbar"):
            col_dl, col_pop, col_edit, col_fs = st.columns(4)
            
            with col_dl:
                st.download_button("", data=csv_data, file_name='attendance_records.csv', mime='text/csv', icon=":material/download:", help="Download CSV")
                if is_first_time:
                    st.markdown('<div class="first-time-label">⬇ Download</div>', unsafe_allow_html=True)
                
            with col_pop:
                with st.popover("", icon=":material/visibility:", help="Show / Hide Columns"):
                    st.markdown("<h4 style='color:#ffffff; margin-top:0; margin-bottom:14px; font-family:Outfit,sans-serif; font-size:1.05rem;'>Display Columns</h4>", unsafe_allow_html=True)
                    temp_selected = []
                    for col in all_cols:
                        is_checked = st.checkbox(col, value=(col in selected_cols), key=f"pop_chk_{col}")
                        if is_checked:
                            temp_selected.append(col)
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("Apply", type="primary", use_container_width=True, key="btn_apply_cols"):
                        st.session_state.cols_select = temp_selected
                        st.rerun()
                if is_first_time:
                    st.markdown('<div class="first-time-label">👁 Show/Hide</div>', unsafe_allow_html=True)
                    
            with col_edit:
                if st.button("", icon=":material/edit:", help="Edit Attendance", key="btn_edit_trigger"):
                    st.session_state.show_edit_panel = not st.session_state.get('show_edit_panel', False)
                    st.rerun()
                if is_first_time:
                    st.markdown('<div class="first-time-label">✏ Edit</div>', unsafe_allow_html=True)
                    
            with col_fs:
                is_fs = st.session_state.get('full_screen_records', False)
                fs_icon = ":material/fullscreen_exit:" if is_fs else ":material/fullscreen:"
                fs_help = "Exit Full Screen" if is_fs else "Full Screen"
                if st.button("", icon=fs_icon, help=fs_help, key="btn_fs_trigger"):
                    st.session_state.full_screen_records = not is_fs
                    st.rerun()
                if is_first_time:
                    st.markdown('<div class="first-time-label">⛶ Full Screen</div>', unsafe_allow_html=True)

    # 3. Render Custom Table
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if not selected_cols:
        st.warning("Please select at least one column to display.")
    else:
        table_html = df_to_custom_html(display_df)
        st.markdown(table_html, unsafe_allow_html=True)


def render_edit_attendance_panel():
    teacher_id = st.session_state.teacher_data['teacher_id']
    
    st.markdown('<div id="edit-attendance-section"></div>', unsafe_allow_html=True)
    st.markdown("""
        <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="
            const doc = window.parent ? window.parent.document : document;
            let attempts = 0;
            const scrollInterval = setInterval(() => {
                const card = doc.querySelector('.st-key-edit_attendance_card');
                if (card) {
                    clearInterval(scrollInterval);
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } else if (++attempts > 30) {
                    clearInterval(scrollInterval);
                    const el = doc.getElementById('edit-attendance-section');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            }, 50);
        " style="display:none;"/>
    """, unsafe_allow_html=True)
    
    # CSS overrides for the edit attendance card
    st.markdown("""
        <style>
        @keyframes highlightPulse {
            0% { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 0 0 0px rgba(37, 99, 235, 0.6); }
            50% { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 0 0 10px rgba(37, 99, 235, 0); }
            100% { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 0 0 0px rgba(37, 99, 235, 0); }
        }
        .st-key-edit_attendance_card {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 24px !important;
            margin-top: 20px !important;
            animation: highlightPulse 1.5s ease-in-out 2 !important;
        }
        
        .st-key-edit_attendance_card p, 
        .st-key-edit_attendance_card h3, 
        .st-key-edit_attendance_card span, 
        .st-key-edit_attendance_card label {
            color: #000000 !important;
        }

        .st-key-student_list_container {
            border: 1px solid #f1f5f9 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            margin-top: 16px !important;
        }

        .st-key-student_list_container div[data-testid="column"] {
            display: flex !important;
            align-items: center !important;
        }

        .st-key-student_list_container > div > div > div[data-testid="element-container"] {
            border-bottom: 1px solid #f1f5f9 !important;
            padding: 10px 16px !important;
            transition: background-color 0.2s ease !important;
            margin: 0 !important;
        }

        .st-key-student_list_container > div > div > div[data-testid="element-container"]:last-child {
            border-bottom: none !important;
        }

        .st-key-student_list_container > div > div > div[data-testid="element-container"]:nth-child(even) {
            background-color: #f8fafc !important;
        }

        .st-key-student_list_container > div > div > div[data-testid="element-container"]:hover {
            background-color: #f1f5f9 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container(key="edit_attendance_card"):
        st.markdown('<h3 style="color:#000000; margin:0 0 16px 0;">📝 Edit Attendance</h3>', unsafe_allow_html=True)
        
        # Select subject
        subjects = get_teacher_subjects(teacher_id)
        if not subjects:
            st.info("No subjects found. Create one first.")
            return
            
        sub_options = {f"{s['name']} ({s['subject_code']})": s['subject_id'] for s in subjects}
        selected_sub_name = st.selectbox("Select Subject to Edit", options=list(sub_options.keys()))
        selected_sub_id = sub_options[selected_sub_name]
        
        # Get unique timestamps/sessions for this subject
        logs_res = supabase.table('attendance_logs').select('timestamp').eq('subject_id', selected_sub_id).execute().data
        timestamps = sorted(list(set(log['timestamp'] for log in logs_res)), reverse=True)
        
        if not timestamps:
            st.info("No attendance sessions found for this subject.")
        else:
            selected_ts = st.selectbox("Select Session Date/Time to Edit", options=timestamps, format_func=lambda x: datetime.fromisoformat(x).strftime("%Y-%m-%d %I:%M %p"))
            
            # Load students and their status
            from src.database.db import get_attendance_for_subject_date, update_attendance_status
            student_records = get_attendance_for_subject_date(selected_sub_id, selected_ts)
            
            if not student_records:
                st.info("No students enrolled or found for this session.")
            else:
                # Calculate session summary metrics
                total_students = len(student_records)
                present_count = sum(1 for r in student_records if r['is_present'])
                absent_count = total_students - present_count
                
                dt = datetime.fromisoformat(selected_ts)
                date_str = dt.strftime("%B %d, %Y")
                time_str = dt.strftime("%I:%M %p")
                
                # Render Session Summary Container
                st.markdown("<hr style='margin:16px 0; border:none; border-top:1px solid #e2e8f0;'/>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#000000; margin:0 0 12px 0;">📊 Session Summary</h4>', unsafe_allow_html=True)
                
                sum_col1, sum_col2, sum_col3 = st.columns(3)
                with sum_col1:
                    st.markdown(f"<span style='color:#64748b; font-size:0.85rem;'>Subject</span><br><strong style='color:#000000; font-size:0.95rem;'>{selected_sub_name}</strong>", unsafe_allow_html=True)
                    st.markdown(f"<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:#64748b; font-size:0.85rem;'>Date</span><br><strong style='color:#000000; font-size:0.95rem;'>{date_str}</strong>", unsafe_allow_html=True)
                with sum_col2:
                    st.markdown(f"<span style='color:#64748b; font-size:0.85rem;'>Time</span><br><strong style='color:#000000; font-size:0.95rem;'>{time_str}</strong>", unsafe_allow_html=True)
                    st.markdown(f"<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:#64748b; font-size:0.85rem;'>Total Students</span><br><strong style='color:#000000; font-size:0.95rem;'>👤 {total_students}</strong>", unsafe_allow_html=True)
                with sum_col3:
                    st.markdown(f"<span style='color:#16a34a; font-size:0.85rem;'>Present</span><br><strong style='color:#16a34a; font-size:0.95rem;'>✅ {present_count}</strong>", unsafe_allow_html=True)
                    st.markdown(f"<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:#dc2626; font-size:0.85rem;'>Absent</span><br><strong style='color:#dc2626; font-size:0.95rem;'>❌ {absent_count}</strong>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin:16px 0; border:none; border-top:1px solid #e2e8f0;'/>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#000000; margin:0 0 8px 0;">👥 Attendance for Selected Session</h4>', unsafe_allow_html=True)
                
                # Use a form to submit updates
                with st.form("edit_attendance_form", border=False):
                    changes = {}
                    
                    with st.container(key="student_list_container"):
                        for r in student_records:
                            col_s, col_p = st.columns([5, 1], vertical_alignment="center")
                            with col_s:
                                st.markdown(f'<span style="font-size:0.95rem; font-weight:600; color:#1e293b;">👤 {r["name"]}</span><br><span style="font-size:0.8rem; color:#64748b; margin-left:22px;">Student ID: {r["student_id"]}</span>', unsafe_allow_html=True)
                            with col_p:
                                # Bind checkbox key to subject & timestamp to avoid stale state caching
                                changes[r['student_id']] = st.checkbox("Present", value=r['is_present'], key=f"edit_att_{selected_sub_id}_{selected_ts}_{r['student_id']}", label_visibility="collapsed")
                    
                    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                    save_btn = st.form_submit_button("Save Changes", use_container_width=True, type="primary")
                    
                    if save_btn:
                        for s_id, is_pres in changes.items():
                            update_attendance_status(s_id, selected_sub_id, selected_ts, is_pres)
                            
                        # Styled save success notice
                        _SAVE_SUCCESS_HTML = """
                        <div style="display: flex; align-items: center; gap: 12px; padding: 12px 20px; background-color: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; margin-top: 12px; animation: slideIn 0.3s ease-out;">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52" style="width: 24px; height: 24px; border-radius: 50%; stroke-width: 4; stroke: #10b981; fill: none; stroke-miterlimit: 10;">
                            <circle cx="26" cy="26" r="25" fill="none" style="stroke-dasharray: 166; stroke-dashoffset: 166; stroke-width: 4; stroke: #10b981; animation: stroke 0.4s cubic-bezier(0.65, 0, 0.45, 1) forwards;"/>
                            <path fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8" style="stroke-dasharray: 48; stroke-dashoffset: 48; stroke-linecap: round; animation: stroke 0.2s cubic-bezier(0.65, 0, 0.45, 1) 0.4s forwards;"/>
                          </svg>
                          <span style="color: #065f46; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 0.95rem;">✅ Attendance Updated Successfully</span>
                        </div>
                        <style>
                        @keyframes stroke { 100% { stroke-dashoffset: 0; } }
                        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
                        </style>
                        """
                        st.markdown(_SAVE_SUCCESS_HTML, unsafe_allow_html=True)
                        time.sleep(1.5)
                        st.rerun()


def teacher_tab_attendance_records():
    # If in full screen mode, show the title
    if st.session_state.get('full_screen_records', False):
        st.markdown('<h2 style="color:#36454F;">Full Screen Attendance Records</h2>', unsafe_allow_html=True)
        st.divider()
        render_records_table_view()
        
        # Render edit panel conditionally in full screen mode
        if st.session_state.get('show_edit_panel', False):
            st.divider()
            render_edit_attendance_panel()
        return

    st.markdown('<h2 style="color:#36454F;">Attendance Records</h2>', unsafe_allow_html=True)
    
    # Render table first
    render_records_table_view()
    
    # Render edit panel conditionally
    if st.session_state.get('show_edit_panel', False):
        st.divider()
        render_edit_attendance_panel()


def login_teacher(username, password):
    if not username or not password:
        return False
    
    teacher = teacher_login(username, password)

    if teacher:
        st.session_state.user_role ='teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        from src.database.db import register_user_session
        register_user_session('teacher', teacher['teacher_id'])
        return True
    

    return False


def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.markdown('<h2 style="color:#36454F; text-align:center;">Login using password</h2>', unsafe_allow_html=True)
    st.space()
    st.space()

    if "failed_login_attempts" not in st.session_state:
        st.session_state.failed_login_attempts = 0

    with st.form("teacher_login_form", border=False):
        teacher_username = st.text_input("Enter username or email", placeholder='ananyaroy', autocomplete="username")
        teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password", autocomplete="current-password")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button('Login', icon=':material/passkey:', use_container_width=True)

    if submitted:
        if login_teacher(teacher_username, teacher_pass):
            st.session_state.failed_login_attempts = 0
            st.toast("welcome back!", icon="👋")
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.failed_login_attempts += 1
            st.error("Invalid username and password combo")

    # If 2 or more consecutive failed attempts, show forgot password flow option
    if st.session_state.failed_login_attempts >= 2:
        st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
        if st.button("Forgot Password?", type="secondary", key="forgot_password_trigger", use_container_width=True):
            reset_password_dialog()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button('Register Instead', icon=':material/passkey:', use_container_width=True):
        st.session_state.teacher_login_type = 'register'
        st.rerun()

    # Add study.svg in bottom right corner
    import base64
    import os
    try:
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        svg_path = os.path.join(assets_dir, "study.svg")
        with open(svg_path, "rb") as f:
            svg_base64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(f"""
            <img src="data:image/svg+xml;base64,{svg_base64}" style="position:fixed; bottom:20px; right:20px; width:300px; pointer-events:none; z-index:10; opacity:0.8; mix-blend-mode:multiply;" />
        """, unsafe_allow_html=True)
    except Exception:
        pass

    footer_dashboard()


@st.dialog("Reset Password")
def reset_password_dialog():
    st.write("Enter your registered email and a new password to reset your credentials.")
    with st.form("reset_password_form", border=False):
        email = st.text_input("Registered Email", placeholder="email@example.com")
        new_pass = st.text_input("New Password", type="password", placeholder="Enter new password")
        confirm_pass = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
        submit = st.form_submit_button("Reset Password", use_container_width=True)
        
    if submit:
        if not email or not new_pass or not confirm_pass:
            st.error("All fields are required!")
        elif new_pass != confirm_pass:
            st.error("Passwords do not match!")
        else:
            from src.database.db import reset_teacher_password
            # Reset password in the database
            reset_teacher_password(email, new_pass)
            # Generic success message to prevent user enumeration
            st.success("If this email is registered, your password has been successfully reset. Please log in.")
            import time
            time.sleep(2.5)
            st.rerun()


def register_teacher(teacher_username, teacher_email, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_email or not teacher_name or not teacher_pass:
        return False, "All Fields are required!"
    if "@" not in teacher_email or "." not in teacher_email:
        return False, "Invalid email address format"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken"
    from src.database.db import check_email_exists
    if check_email_exists(teacher_email):
        return False, "Email already registered"
    if teacher_pass != teacher_pass_confirm:
        return False, "Password doesn't match"
    
    try:
        create_teacher(teacher_username, teacher_pass, teacher_name, teacher_email)
        return True, "Sucessfully Created! Login Now"
    except Exception as e:
        return False, "Unexpected Error!"
    

def check_password_strength(password):
    import re
    has_min_len = len(password) >= 8
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'[0-9]', password))
    has_special = bool(re.search(r'[@$!%*?&]', password))
    no_spaces = ' ' not in password and len(password) > 0
    only_valid = bool(re.match(r'^[A-Za-z0-9@$!%*?&]*$', password)) if password else False
    
    score = sum([has_min_len, has_upper, has_lower, has_digit, has_special, no_spaces, only_valid])
    
    if not password:
        strength = "None"
        color = "#cbd5e1"
        pct = 0
    elif score < 4:
        strength = "Weak"
        color = "#ef4444"
        pct = 33
    elif score < 7:
        strength = "Medium"
        color = "#f97316"
        pct = 66
    else:
        strength = "Strong"
        color = "#22c55e"
        pct = 100
        
    return {
        "score": score,
        "strength": strength,
        "color": color,
        "pct": pct,
        "has_min_len": has_min_len,
        "has_upper": has_upper,
        "has_lower": has_lower,
        "has_digit": has_digit,
        "has_special": has_special,
        "no_spaces": no_spaces,
        "only_valid": only_valid
    }


def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.markdown('<h2 style="color:#36454F;">Register your teacher profile</h2>', unsafe_allow_html=True)

    st.space()
    st.space()

    # Use regular input fields outside form for real-time validation reactivity
    teacher_username = st.text_input("Enter username", placeholder='ananyaroy')
    teacher_email = st.text_input("Enter email", placeholder='ananya@school.edu')
    teacher_name = st.text_input("Enter name", placeholder='Ananya Roy')
    
    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")
    
    res = check_password_strength(teacher_pass)
    
    strength_feedback = ""
    if res['strength'] == "Weak":
        strength_feedback = "🔴 Weak"
    elif res['strength'] == "Medium":
        strength_feedback = "🟠 Medium"
    elif res['strength'] == "Strong":
        strength_feedback = "🟢 Strong"
        
    st.markdown(f"""
    <div style="background-color: #f1f5f9; border-radius: 8px; height: 8px; width: 100%; margin-top: 8px; overflow: hidden;">
      <div style="background-color: {res['color']}; width: {res['pct']}%; height: 100%; transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s ease;"></div>
    </div>
    <p style="font-size: 0.85rem; font-weight: bold; color: {res['color']}; margin-top: 4px; margin-bottom: 12px;">{strength_feedback}</p>
    """, unsafe_allow_html=True)

    teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Enter password")
    
    st.markdown("<div style='font-size:12px; height:15px;'></div>", unsafe_allow_html=True)
    submitted = st.button('Register now', use_container_width=True)
    
    if submitted:
        if ' ' in teacher_pass or ' ' in teacher_pass_confirm:
            st.error("Password cannot contain spaces!")
        elif res['score'] < 7:
            st.error("Please satisfy all password requirements first!")
        else:
            success, message = register_teacher(teacher_username, teacher_email, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    st.space()
    if st.button('Login Instead', type="primary", icon=':material/passkey:', use_container_width=True):
        st.session_state.teacher_login_type = 'login'
        st.rerun()


def teacher_tab_qr_attendance():
    st.markdown('<h2 style="color:#36454F;">QR Attendance</h2>', unsafe_allow_html=True)
    teacher_id = st.session_state.teacher_data['teacher_id']
    
    if not st.session_state.get('qr_active', False):
        subjects = get_teacher_subjects(teacher_id)
        if not subjects:
            st.warning('You haven\'t created any subjects yet!')
            return
            
        subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}
        
        st.markdown("""
            <style>
                div[data-testid="stSelectbox"] label p {
                    color: #36454F !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1], vertical_alignment='bottom')
        with col1:
            selected_subject_label = st.selectbox('Select Subject for QR', options=list(subject_options.keys()))
        with col2:
            start_btn = st.button('Start QR Attendance', type='primary', width='stretch')
            
        if start_btn:
            import time
            from datetime import datetime
            st.session_state.qr_active = True
            st.session_state.qr_subject_id = subject_options[selected_subject_label]
            st.session_state.qr_subject_name = selected_subject_label.split(" - ")[0]
            st.session_state.qr_session_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            st.session_state.qr_token_expiry = time.time() + 20
            
            from src.pipelines.qr_pipeline import generate_qr_token
            st.session_state.qr_current_token = generate_qr_token(
                st.session_state.qr_subject_id,
                time.time(),
                "session_key_placeholder",
                st.session_state.qr_session_timestamp
            )
            st.rerun()
            
    else:
        import time
        now = time.time()
        expiry = st.session_state.get('qr_token_expiry', 0)
        remaining = int(expiry - now)
        
        if remaining <= 0:
            from src.pipelines.qr_pipeline import generate_qr_token
            st.session_state.qr_token_expiry = time.time() + 20
            st.session_state.qr_current_token = generate_qr_token(
                st.session_state.qr_subject_id,
                time.time(),
                "session_key_placeholder",
                st.session_state.qr_session_timestamp
            )
            remaining = 20
            st.rerun()
            
        st.write(f"### Active Session for **{st.session_state.qr_subject_name}**")
        st.info("Ask students to scan this QR code using the 'Scan QR' button on their dashboard.")
        
        from src.pipelines.qr_pipeline import generate_qr_image
        qr_img_bytes = generate_qr_image(st.session_state.qr_current_token)
        
        c_left, c_mid, c_right = st.columns([1, 2, 1])
        with c_mid:
            st.image(qr_img_bytes, width=280)
            st.markdown(f"""
            <div style="display:flex; justify-content:center; margin: 12px 0 4px 0;">
              <div style="background: #1e293b; border-radius: 14px; padding: 12px 28px; display:inline-block; box-shadow: 0 4px 16px rgba(30,41,59,0.18);">
                <span style="font-family: 'Courier New', monospace; font-size: 2.6rem; font-weight: 900; letter-spacing: 12px; color: #f8fafc; user-select: all; text-transform: uppercase;">{st.session_state.qr_current_token}</span>
              </div>
            </div>
            <p style="text-align:center; color:#64748b; font-size:0.78rem; margin:2px 0 0 0; font-family:'Outfit',sans-serif;">6-character attendance code</p>
            """, unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: #36454F;'>Refreshing QR in <span style='color:#EB459E;'>{remaining}s</span></h3>", unsafe_allow_html=True)
            
            if st.button('Stop QR Attendance', type='secondary', width='stretch'):
                st.session_state.qr_active = False
                st.rerun()
                
        time.sleep(1)
        st.rerun()