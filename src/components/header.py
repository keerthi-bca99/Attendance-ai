import streamlit as st
import base64
import os

def get_logo_data():
    try:
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        logo_path = os.path.join(assets_dir, "study.svg")
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/svg+xml;base64,{logo_base64}"
    except Exception:
        return "https://i.ibb.co/YTYGn5qV/logo.png"

def header_home():

    logo_url = get_logo_data()
    
    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:30px; margin-top:30px">
            <img src='{logo_url}' style='height:160px;' />
            <h1 style='text-align:center; color:#36454F; margin-bottom: 5px; white-space: nowrap;'>ATTEND<br/>IQ</h1>
            <span style='color:#36454F; font-family:sans-serif; font-size:0.9rem; font-weight:600; background:rgba(54,69,79,0.1); padding:2px 8px; border-radius:12px;'>v2.0.0</span>
        </div>   
                
                """, unsafe_allow_html=True)


def header_dashboard():

    logo_url = get_logo_data()
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; gap:10px">
            <img src='{logo_url}' style='height:120px;' />
            <div>
                <h2 style='text-align:left; color:#36454F; margin:0; line-height:1.1; white-space: nowrap; font-size: 1.8rem !important;'>ATTEND<br/>IQ</h2>
                <span style='color:#36454F; font-family:sans-serif; font-size:0.75rem; font-weight:600; background:rgba(54,69,79,0.1); padding:1px 6px; border-radius:10px;'>v2.0.0</span>
            </div>
        </div>   
                
                """, unsafe_allow_html=True)
