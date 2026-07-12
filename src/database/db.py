from src.database.config import supabase
import bcrypt

def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username):
    # Check for unique username, returns true when username is already taken
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0 


def check_email_exists(email):
    # Check for unique email, returns true when email is already taken
    response = supabase.table("teachers").select("email").eq("email", email.strip().lower()).execute()
    return len(response.data) > 0


def create_teacher(username, password, name, email):
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name,
        "email": email.strip().lower()
    }
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username_or_email, password):
    # Support login with either username or email
    val = username_or_email.strip().lower()
    if "@" in val:
        response = supabase.table("teachers").select("*").eq("email", val).execute()
    else:
        response = supabase.table("teachers").select("*").eq("username", username_or_email).execute()

    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None


def reset_teacher_password(email, new_password):
    email_clean = email.strip().lower()
    hashed = hash_pass(new_password)
    response = supabase.table("teachers").update({"password": hashed}).eq("email", email_clean).execute()
    return len(response.data) > 0


def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data


def create_student(new_name, face_embedding=None):
    data = {'name': new_name, 'face_embedding': face_embedding}
    response = supabase.table('students').insert(data).execute()
    return response.data


def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data


def get_teacher_subjects(teacher_id):
    response = supabase.table('subjects').select("*, subject_students(count), attendance_logs(timestamp)").eq("teacher_id", teacher_id).execute()
    subjects = response.data

    for sub in subjects:
        sub['total_students'] = sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendance = sub.get('attendance_logs', [])
        unique_sessions = len(set(log['timestamp'] for log in attendance))
        sub['total_classes'] = unique_sessions

        sub.pop('subject_students', None)
        sub.pop('attendance_logs', None)

    return subjects


def enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, "subject_id": subject_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id, subject_id):
    response = supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data


def get_student_subjects(student_id):
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data


def sync_attendance_summary(logs):
    """After inserting into attendance_logs, update attendance_summary.
    For each log entry, upsert a row in attendance_summary keyed on
    (student_id, subject_id).
    """
    for log in logs:
        student_id = log['student_id']
        subject_id = log['subject_id']
        is_present = bool(log.get('is_present', False))

        existing = (
            supabase.table('attendance_summary')
            .select('present_count')
            .eq('student_id', student_id)
            .eq('subject_id', subject_id)
            .execute()
        ).data

        if existing:
            row = existing[0]
            new_count = row['present_count'] + (1 if is_present else 0)
            supabase.table('attendance_summary').update(
                {'present_count': new_count}
            ).eq('student_id', student_id).eq('subject_id', subject_id).execute()
        else:
            supabase.table('attendance_summary').insert({
                'student_id': student_id,
                'subject_id': subject_id,
                'present_count': 1 if is_present else 0,
            }).execute()


def get_attendance_summary(student_id):
    response = (
        supabase.table('attendance_summary')
        .select('*, subjects(*)')
        .eq('student_id', student_id)
        .execute()
    )
    return response.data


def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*, teachers(name)), students(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data


def check_qr_attendance_already_marked(student_id, subject_id, timestamp):
    response = supabase.table('attendance_logs').select('*').eq('student_id', student_id).eq('subject_id', subject_id).eq('timestamp', timestamp).execute()
    return len(response.data) > 0


def get_students_for_subject(subject_id):
    """Get all students enrolled in a subject."""
    response = supabase.table('subject_students').select('*, students(*)').eq('subject_id', subject_id).execute()
    return [item['students'] for item in response.data if item.get('students')]


def get_attendance_for_subject_date(subject_id, timestamp):
    """Get all students and their attendance status for a specific subject and timestamp."""
    # 1. Fetch enrolled students
    enrolled = get_students_for_subject(subject_id)
    # 2. Fetch log entries for this timestamp
    logs = supabase.table('attendance_logs').select('*').eq('subject_id', subject_id).eq('timestamp', timestamp).execute().data
    
    log_map = {log['student_id']: log['is_present'] for log in logs}
    
    records = []
    for student in enrolled:
        records.append({
            'student_id': student['student_id'],
            'name': student['name'],
            'is_present': log_map.get(student['student_id'], False)
        })
    return records


def update_attendance_status(student_id, subject_id, timestamp, is_present):
    # 1. Get the current status from attendance_logs
    existing = supabase.table('attendance_logs').select('is_present').eq('student_id', student_id).eq('subject_id', subject_id).eq('timestamp', timestamp).execute().data
    
    if not existing:
        # If record doesn't exist, insert it
        data = {
            'student_id': student_id,
            'subject_id': subject_id,
            'timestamp': timestamp,
            'is_present': is_present
        }
        supabase.table('attendance_logs').insert(data).execute()
        # Update summary
        _adjust_attendance_summary(student_id, subject_id, was_present=False, is_present=is_present)
    else:
        was_present = bool(existing[0]['is_present'])
        if was_present != is_present:
            # Update record
            supabase.table('attendance_logs').update({'is_present': is_present}).eq('student_id', student_id).eq('subject_id', subject_id).eq('timestamp', timestamp).execute()
            # Update summary
            _adjust_attendance_summary(student_id, subject_id, was_present=was_present, is_present=is_present)


def _adjust_attendance_summary(student_id, subject_id, was_present, is_present):
    existing = supabase.table('attendance_summary').select('present_count').eq('student_id', student_id).eq('subject_id', subject_id).execute().data
    
    diff = 0
    if was_present and not is_present:
        diff = -1
    elif not was_present and is_present:
        diff = 1
        
    if existing:
        new_count = max(0, existing[0]['present_count'] + diff)
        supabase.table('attendance_summary').update({'present_count': new_count}).eq('student_id', student_id).eq('subject_id', subject_id).execute()
    else:
        new_count = 1 if is_present else 0
        supabase.table('attendance_summary').insert({
            'student_id': student_id,
            'subject_id': subject_id,
            'present_count': new_count
        }).execute()


import uuid
import json
import os
import streamlit as st

USER_SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_user_sessions.json")

def register_user_session(user_type, user_id):
    token = str(uuid.uuid4())
    key = f"{user_type}_{user_id}"
    try:
        data = {}
        if os.path.exists(USER_SESSIONS_FILE):
            with open(USER_SESSIONS_FILE, "r") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        data[key] = token
        with open(USER_SESSIONS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error registering user session: {e}")
    st.session_state.active_session_token = token
    return token

def verify_user_session(user_type, user_id):
    if "active_session_token" not in st.session_state:
        return False
    key = f"{user_type}_{user_id}"
    try:
        if not os.path.exists(USER_SESSIONS_FILE):
            return True
        with open(USER_SESSIONS_FILE, "r") as f:
            data = json.load(f)
        active_token = data.get(key)
        return active_token == st.session_state.active_session_token
    except Exception:
        return True
