import streamlit as st
def subject_card(name, code, section, stats=None, footer_callback=None):
    html = f"""
        <div style="background: #ffffff; border-left: 6px solid #EB459E; padding:25px; border-radius: 20px; border: 1px solid #e2e8f0; margin-bottom:20px;">
        <h3 style="margin:0; color: #000000; font-size: 1.5rem; font-weight:700;">{name}</h3>
        <p style="color:#64748b; margin:10px 0 16px 0;">Code : <span style="background:#E0E3FF; color:#5865F2; padding:2px 10px; border-radius:6px; font-weight:600;">{code}</span> &nbsp;|&nbsp; Section : <span style="color:#1e293b;">{section}</span></p>
        """
    
    if stats:
        html+= """
        <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:8px;">
        """
        for icon, label, value in stats:
            html+= f'<div style="background: #fdf2f8; border: 1px solid #f9c0e0; padding:8px 16px; border-radius:12px; font-size:0.95rem; font-weight:500;">{icon} <b style="color:#EB459E; font-size:1.1rem;">{value}</b> <span style="color:#000000;">{label}</span></div>'
        
        html+= "</div>"

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()
