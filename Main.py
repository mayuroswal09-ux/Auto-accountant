import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from datetime import datetime, date
from PIL import Image
import io

# ==========================================
# 1. CORE ENGINE & UI ARCHITECTURE
# ==========================================
st.set_page_config(page_title="OSWAL OMNI ERP", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #ffd700; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }
    .stSidebar { background: #010409 !important; border-right: 2px solid #ffd700; }
    .stButton>button { background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%); color: black; font-weight: 800; border: none; border-radius: 8px; width: 100%; height: 48px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #ffd700; }
    h1, h2, h3 { color: #ffd700 !important; font-weight: 800 !important; }
    .report-card { border-left: 5px solid #ffd700; background: #1c2128; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; padding: 10px 20px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #ffd700 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CLOUD INFRASTRUCTURE INITIALIZATION
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "active_co_id" not in st.session_state: st.session_state.active_co_id = None

# ==========================================
# 3. SECURITY GATEWAY (AUTHENTICATION)
# ==========================================
def login_screen():
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>🏆 OSWAL OMNIPOTENCE ERP</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,
