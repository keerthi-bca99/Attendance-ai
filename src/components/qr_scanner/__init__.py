import streamlit.components.v1 as components
import os

parent_dir = os.path.dirname(os.path.abspath(__file__))
qr_scanner = components.declare_component("qr_scanner", path=parent_dir)
