import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime, date
from PIL import Image
import io

# ==========================================
# 1. CORE ENGINE & UI ARCHITECTURE
# ==========================================
st.set_page_config(page_title="OSWAL OMNI ERP", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dark Mode Professional UI
st.markdown("""
    <style>
    .stApp { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #ffd700; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }
    .stSidebar { background: #010409 !important; border-right: 2px solid #ffd700; }
    .stButton>button { background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%); color: black; font-weight: 800; border: none; border-radius: 8px; width: 100%; height: 48px; }
    h1, h2, h3 { color: #ffd700 !important; font-weight: 800 !important; }
    .report-card { border-left: 5px solid #ffd700; background: #1c2128; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffd700 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CLOUD INFRASTRUCTURE INITIALIZATION
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "active_co_id" not in st.session_state: st.session_state.active_co_id = None

# ==========================================
# 3. AUTHENTICATION MODULE
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 80px;'>🏆 OSWAL OMNIPOTENCE ERP</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        u = st.text_input("Administrator Identity").strip().lower()
        p = st.text_input("Security Access Key", type="password")
        if st.button("INITIALIZE ENTERPRISE SYSTEMS"):
            if u == "mayur" and p == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Access Forbidden")
else:
    # ==========================================
    # 4. GLOBAL DATA ENGINE (RELATIONAL)
    # ==========================================
    co_res = supabase.table("companies").select("*").execute()
    co_df = pd.DataFrame(co_res.data)
    
    st.sidebar.markdown("### 🏢 CORPORATE SECTOR")
    if co_df.empty:
        st.sidebar.warning("No Entities Detected.")
        sel_co_name = "None"
    else:
        sel_co_name = st.sidebar.selectbox("Active Entity", co_df['name'].tolist())
        st.session_state.active_co_id = co_df[co_df['name'] == sel_co_name]['id'].values[0]

    nav = [
        "📊 Executive Dashboard", "🏛️ Master Setup & Opening", "📝 Smart Voucher Entry", 
        "🔍 Day Book", "📦 Inventory Control", "⚖️ Final Accounts (P&L/BS)", 
        "🧾 Receivables/Payables", "🛡️ Forensic Integrity Audit", "⚙️ Settings"
    ]
    choice = st.sidebar.radio("Navigation Gate", nav)

    # --- MODULE: DASHBOARD ---
    if choice == "📊 Executive Dashboard":
        st.title(f"Command Center: {sel_co_name}")
        if st.session_state.active_co_id:
            v_res = supabase.table("vouchers").select("*").eq("company_id", st.session_state.active_co_id).execute()
            v_df = pd.DataFrame(v_res.data)
            if not v_df.empty:
                c1, c2, c3, c4 = st.columns(4)
                sales = v_df[v_df['vouch_type']=='Sales']['total_amount'].sum()
                purch = v_df[v_df['vouch_type']=='Purchase']['total_amount'].sum()
                c1.metric("Gross Revenue", f"₹{sales:,.2f}")
                c2.metric("Procurement", f"₹{purch:,.2f}")
                c3.metric("Net Flow", f"₹{sales-purch:,.2f}")
                c4.metric("Transactions", len(v_df))
                
                fig = px.area(v_df, x='date', y='total_amount', color='vouch_type', template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

    # --- MODULE: MASTERS ---
    elif choice == "🏛️ Master Setup & Opening":
        st.header("Corporate Master Management")
        
        tab1, tab2, tab3 = st.tabs(["Companies", "Ledgers", "Inventory Items"])
        with tab1:
            with st.form("c_m"):
                cn = st.text_input("Entity Name"); cg = st.text_input("GSTIN")
                if st.form_submit_button("🔨 CREATE"):
                    supabase.table("companies").insert({"name":cn, "gstin":cg}).execute(); st.rerun()
        with tab2:
            if st.session_state.active_co_id:
                g_res = supabase.table("account_groups").select("*").execute()
                g_df = pd.DataFrame(g_res.data)
                with st.form("l_m"):
                    ln = st.text_input("Ledger Name")
                    lg = st.selectbox("Group", g_df['name'].tolist())
                    ob = st.number_input("Opening Balance")
                    if st.form_submit_button("🔨 SYNC"):
                        gid = g_df[g_df['name']==lg]['id'].values[0]
                        supabase.table("ledgers").insert({"company_id":st.session_state.active_co_id, "name":ln, "group_id":gid, "opening_balance":ob}).execute()
                        st.success("Ledger Created.")
        with tab3:
            if st.session_state.active_co_id:
                with st.form("s_m"):
                    sn = st.text_input("Item Name"); su = st.selectbox("Unit", ["Pcs", "Kg", "Mtr"])
                    if st.form_submit_button("📦 ADD STOCK"):
                        supabase.table("stock_items").insert({"company_id":st.session_state.active_co_id, "name":sn, "unit":su}).execute(); st.success("Added.")

    # --- MODULE: SMART VOUCHER ---
    elif choice == "📝 Smart Voucher Entry":
        st.header(f"Unified Entry Suite: {sel_co_name}")
        
        if st.session_state.active_co_id:
            led_res = supabase.table("ledgers").select("id, name").eq("company_id", st.session_state.active_co_id).execute()
            led_df = pd.DataFrame(led_res.data)
            if led_df.empty: st.error("Add Ledgers First!")
            else:
                with st.form("v_f", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    vt = c1.selectbox("Type", ["Sales", "Purchase", "Payment", "Receipt", "Contra", "Journal"])
                    vd = c2.date_input("Date")
                    dr = st.selectbox("Debit Ledger (By)", led_df['name'].tolist())
                    cr = st.selectbox("Credit Ledger (To)", led_df['name'].tolist())
                    amt = st.number_input("Amount", min_value=0.01)
                    nar = st.text_area("Narration")
                    if st.form_submit_button("🚀 POST TRANSACTION"):
                        did = led_df[led_df['name']==dr]['id'].values[0]
                        cid = led_df[led_df['name']==cr]['id'].values[0]
                        vh = supabase.table("vouchers").insert({"company_id":st.session_state.active_co_id, "vouch_no":"AUTO", "vouch_type":vt, "date":str(vd), "total_amount":amt, "narration":nar}).execute()
                        vid = vh.data[0]['id']
                        supabase.table("voucher_entries").insert([{"voucher_id":vid, "ledger_id":did, "debit_amount":amt}, {"voucher_id":vid, "ledger_id":cid, "credit_amount":amt}]).execute()
                        st.success("Synchronized Successfully.")

    # --- MODULE: FINAL ACCOUNTS ---
    elif choice == "⚖️ Final Accounts (P&L/BS)":
        st.header("Financial Position")
        
        if st.session_state.active_co_id:
            res = supabase.table("voucher_entries").select("debit_amount, credit_amount, ledgers(name, company_id)").execute()
            f_df = pd.json_normalize(res.data)
            if not f_df.empty:
                f_df = f_df[f_df['ledgers.company_id'] == st.session_state.active_co_id]
                st.table(f_df.groupby('ledgers.name').agg({'debit_amount':'sum', 'credit_amount':'sum'}))
            else: st.info("No movements.")

    # --- MODULE: FORENSIC AUDIT ---
    elif choice == "🛡️ Forensic Integrity Audit":
        st.header("Forensic Fraud Scanner")
        if st.session_state.active_co_id:
            v_res = supabase.table("vouchers").select("*").eq("company_id", st.session_state.active_co_id).execute()
            v_df = pd.DataFrame(v_res.data)
            if not v_df.empty:
                dupes = v_df[v_df.duplicated(['total_amount', 'date'])]
                if not dupes.empty: st.error(f"⚠️ {len(dupes)} Suspected Duplicate Entries Found!")
                else: st.success("✅ Ledger Integrity Verified.")

    if st.sidebar.button("🔐 LOGOUT"):
        st.session_state.logged_in = False; st.rerun()
