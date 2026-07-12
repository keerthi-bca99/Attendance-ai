import streamlit as st


def header_home():

    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    
    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:30px; margin-top:30px">
            <img src='{logo_url}' style='height:100px;' />
            <h1 style='text-align:center; color:#E0E3FF; margin-bottom: 5px;'>SNAP<br/>CLASS</h1>
            <span style='color:#A0A5E0; font-family:sans-serif; font-size:0.9rem; font-weight:600; background:rgba(224,227,255,0.1); padding:2px 8px; border-radius:12px;'>v2.0.0</span>
        </div>   
                
                """, unsafe_allow_html=True)


def header_dashboard():

    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; gap:10px">
            <img src='{logo_url}' style='height:85px;' />
            <div>
                <h2 style='text-align:left; color:#5865F2; margin:0; line-height:1.1;'>SNAP<br/>CLASS</h2>
                <span style='color:#8892B0; font-family:sans-serif; font-size:0.75rem; font-weight:600; background:rgba(88,101,242,0.1); padding:1px 6px; border-radius:10px;'>v2.0.0</span>
            </div>
        </div>   
                
                """, unsafe_allow_html=True)
