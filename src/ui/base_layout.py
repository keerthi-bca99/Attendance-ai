import streamlit as st



def style_background_home():

    st.markdown("""
        <style>

                .stApp {
                    background: #5865F2 !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color:#E0E3FF !important;
                    padding:2.5rem !important;
                    border-radius: 5rem !important;
                    }
        </style>  

                """
            ,unsafe_allow_html=True)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background: #E0E3FF !important;
                }

        </style>  

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
# asdasd
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

                
         /* Hide Top Bar of streamlit */
                
            #MainMenu, footer, header {
                visibility: hidden;
            }
                
            .block-container {
                padding-top:1.5rem !important;    
            }

            h1 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 3.5rem !important;
                line-height:1.1 !important;
                margin-bottom:0rem !important;
            }
                

            h2 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height:0.9 !important;
                margin-bottom:0rem !important;
            }
                
            h3, h4, p {
                font-family: 'Outfit', sans-serif;
            }
                

            button{
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="secondary"]{
                border-radius: 1.5rem !important;
                background-color: #EB459E !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="tertiary"]{
                border-radius: 1.5rem !important;
                background-color: black !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button:hover{
                transform :scale(1.05)}
                
            /* Hide fullscreen options globally */
            button[title="View fullscreen"],
            button[data-testid="StyledFullScreenButton"],
            div[data-testid="stImage"] button,
            div[data-testid="stImageHoverContainer"] button,
            [data-testid="stElementContainer"] button[title="View fullscreen"],
            [data-testid="stElementContainer"] [data-testid="StyledFullScreenButton"],
            button[kind="elementToolbar"],
            [data-testid="stBaseButton-elementToolbar"],
            [data-testid="stElementToolbarButtonIcon"],
            .st-emotion-cache-1u3gpve {
                display: none !important;
            }
            
            /* Global text input label color */
            div[data-testid="stTextInput"] label p {
                color: #36454F !important;
            }
            
            /* Responsive column layouts for mobile views */
            @media (max-width: 768px) {
                html, body, [data-testid="stAppViewContainer"], .stApp {
                    max-width: 100vw !important;
                    overflow-x: hidden !important;
                }
                div[data-testid="stHorizontalBlock"] {
                    flex-direction: column !important;
                    gap: 12px !important;
                }
                div[data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                }
                /* Keep records action toolbar horizontal on mobile */
                div[data-testid="stVerticalBlock"].st-key-attendance_toolbar div[data-testid="stHorizontalBlock"],
                .st-key-attendance_toolbar div[data-testid="stHorizontalBlock"] {
                    flex-direction: row !important;
                    gap: 8px !important;
                }
                div[data-testid="stVerticalBlock"].st-key-attendance_toolbar div[data-testid="column"],
                .st-key-attendance_toolbar div[data-testid="column"] {
                    width: auto !important;
                    flex: 1 1 0% !important;
                    min-width: 0 !important;
                }
            }
        </style>  

                """
            ,unsafe_allow_html=True)