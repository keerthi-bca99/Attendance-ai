import time
import io
import random
import string
import json
import os
import segno

# File to store temporary active sessions locally to bypass Supabase schema restrictions
SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_sessions.json")


def generate_session_code(length: int = 6) -> str:
    """Generate a unique random alphanumeric session code."""
    # Exclude confusing characters like O, 0, I, 1 for maximum scanning clarity
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


def generate_qr_token(subject_id: str, issued_at: float, session_key: str, session_timestamp: str) -> str:
    """Generate a 6-character session code and store it in active_sessions.json."""
    session_code = generate_session_code()
    expires_at = time.time() + 20
    
    try:
        data = {}
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        
        # Clean up old/expired sessions to keep the JSON file lightweight
        now = time.time()
        data = {c: s for c, s in data.items() if s.get("expires_at", 0) > now}
        
        # Save new active session details
        data[session_code] = {
            "subject_id": int(subject_id),
            "session_timestamp": session_timestamp,
            "expires_at": expires_at
        }
        
        with open(SESSIONS_FILE, "w") as f:
            json.dump(data, f)
            
    except Exception as e:
        print(f"Error registering active session: {e}")
        
    return session_code


def validate_qr_token(token: str, max_age: int = 20):
    """
    Validate a short session code token by reading the local active_sessions.json file.
    
    Returns:
        (is_valid: bool, subject_id: int | None, session_key: None, session_timestamp: str | None, error: str | None)
    """
    try:
        code = token.strip().upper()
        if len(code) != 6:
            return False, None, None, None, "Invalid session code format"
            
        if not os.path.exists(SESSIONS_FILE):
            return False, None, None, None, "Attendance session not found or closed"
            
        with open(SESSIONS_FILE, "r") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
                
        session = data.get(code)
        if not session:
            return False, None, None, None, "Attendance session not found or closed"
            
        if time.time() > session.get("expires_at", 0):
            return False, None, None, None, "Attendance session has expired"
            
        return True, session.get("subject_id"), None, session.get("session_timestamp"), None
        
    except Exception as e:
        return False, None, None, None, f"Session validation error: {str(e)}"


def generate_qr_image(token: str) -> bytes:
    """Generate a high-quality QR code PNG (bytes) containing only the short session code."""
    qr = segno.make_qr(token, error="H")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=8, border=2, dark="#1e293b", light="#f8fafc")
    buf.seek(0)
    return buf.read()


def new_qr_session(subject_id: str, session_timestamp: str):
    """
    Create a brand-new QR session.
    
    Returns:
        (session_code, issued_at, None, image_bytes)
    """
    issued_at = time.time()
    token = generate_qr_token(subject_id, issued_at, "session_key_placeholder", session_timestamp)
    image_bytes = generate_qr_image(token)
    return token, issued_at, None, image_bytes
