import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime, date
from PIL import Image
import io

# ==========================================
# 1. CORE ENGINE & UI STYLING
# ==========================================
st.set_page_config(page_title="OSWAL INFINITY ERP", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #ffd700; border-radius: 12px; padding: 20px; }
    .stSidebar { background: #010409 !important; border-right: 2px solid #ffd700; }
    .stButton>button { background: #ffd700; color: black; font-weight: 800; border: none; border-radius: 8px; width: 100%; height: 45px; }
    h1, h2, h3 { color: #ffd700 !important; }
    .report-card { border-left: 5px solid #ffd700; background: #1c2128; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE INITIALIZATION
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# ==========================================
# 3. AUTHENTICATION MODULE
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>🛡️ OSWAL TITAN LOGIN</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Administrator ID")
        p = st.text_input("Access Key", type="password")
        if st.button("INITIALIZE CORE"):
            if u == "mayur" and p == "1234":
                st.session_state.logged_in = True; st.rerun()
            else: st.error("Access Forbidden.")
else:
    # ==========================================
    # 4. RELATIONAL DATA FETCH (NO ERRORS)
    # ==========================================
    # Fetch all companies to populate the selector
    co_res = supabase.table("companies").select("*").execute()
    co_df = pd.DataFrame(co_res.data)
    
    st.sidebar.markdown("### 🏢 CORPORATE SECTOR")
    if co_df.empty:
        st.sidebar.warning("No Companies Found. Go to Masters.")
        active_co_id = None
        sel_co_name = "None"
    else:
        sel_co_name = st.sidebar.selectbox("Active Entity", co_df['name'].tolist())
        active_co_id = co_df[co_df['name'] == sel_co_name]['id'].values[0]

    # Main Navigation
    nav = [
        "📊 Executive Dashboard", "🏛️ Master Setup & Opening", "📝 Smart Voucher Entry", 
        "🔍 Audit Log & Day Book", "📦 Inventory & Batch Control", "⚖️ Final Accounts (P&L/BS)", 
        "🧾 Receivables & Payables", "🏦 Bank Reconciliation (BRS)", "📈 Advanced Ratio Analysis", 
        "🛡️ Forensic Integrity Audit", "⚙️ System Configuration"
    ]
    choice = st.sidebar.radio("Gateway of Singularity", nav)

    # --- MODULE 1: EXECUTIVE DASHBOARD ---
    if choice == "📊 Executive Dashboard":
        st.title(f"Dashboard: {sel_co_name}")
        if active_co_id:
            # Relational Query: Fetch Vouchers for active_co_id
            v_res = supabase.table("vouchers").select("*").eq("company_id", active_co_id).execute()
            df = pd.DataFrame(v_res.data)
            
            if not df.empty:
                c1, c2, c3 = st.columns(3)
                sales = df[df['vouch_type']=='Sales']['total_amount'].sum()
                purch = df[df['vouch_type']=='Purchase']['total_amount'].sum()
                c1.metric("Revenue", f"₹{sales:,.2f}")
                c2.metric("Procurement", f"₹{purch:,.2f}")
                c3.metric("Net Flow", f"₹{sales-purch:,.2f}")
                
                fig = px.line(df, x='date', y='total_amount', title="Cash Movement Trend")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#ffd700")
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("Ready for first transaction.")

    # --- MODULE 2: MASTER SETUP (LEDGERS & GROUPS) ---
    elif choice == "🏛️ Master Setup & Opening":
        st.header("Master Ledger Creation")
        t1, t2 = st.tabs(["New Company", "New Ledger"])
        
        with t1:
            with st.form("co_form"):
                n = st.text_input("Company Name")
                g = st.text_input("GSTIN")
                a = st.text_area("Address")
                if st.form_submit_button("🔨 Create Entity"):
                    supabase.table("companies").insert({"name": n, "gstin": g, "address": a}).execute()
                    st.success("Entity Hardened."); st.rerun()
        
        with t2:
            if active_co_id:
                # Get Groups from SQL
                grp_res = supabase.table("account_groups").select("*").execute()
                grp_list = pd.DataFrame(grp_res.data)
                
                with st.form("led_form"):
                    ln = st.text_input("Ledger Name")
                    lg = st.selectbox("Select Group", grp_list['name'].tolist())
                    lg_id = grp_list[grp_list['name'] == lg]['id'].values[0]
                    ob = st.number_input("Opening Balance")
                    if st.form_submit_button("🔨 Create Ledger"):
                        supabase.table("ledgers").insert({
                            "company_id": active_co_id, "name": ln, "group_id": lg_id, "opening_balance": ob
                        }).execute()
                        st.success(f"Ledger {ln} Synced.")

    # --- MODULE 3: SMART VOUCHER (RELATIONAL DOUBLE ENTRY) ---
    elif choice == "📝 Smart Voucher Entry":
        st.header(f"Transaction: {sel_co_name}")
        if active_co_id:
            # Fetch ledgers for dropdowns
            led_res = supabase.table("ledgers").select("id, name").eq("company_id", active_co_id).execute()
            led_df = pd.DataFrame(led_res.data)
            
            if led_df.empty:
                st.error("Create ledgers in Masters first!")
            else:
                with st.form("v_entry", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    v_type = c1.selectbox("Voucher Type", ["Sales", "Purchase", "Payment", "Receipt"])
                    v_date = c2.date_input("Date")
                    
                    dr_name = st.selectbox("Debit Ledger", led_df['name'].tolist())
                    cr_name = st.selectbox("Credit Ledger", led_df['name'].tolist())
                    amt = st.number_input("Amount", min_value=0.0)
                    nar = st.text_area("Narration")
                    
                    if st.form_submit_button("🚀 POST TRANSACTION"):
                        dr_id = led_df[led_df['name'] == dr_name]['id'].values[0]
                        cr_id = led_df[led_df['name'] == cr_name]['id'].values[0]
                        
                        # 1. Insert Voucher Header
                        v_head = supabase.table("vouchers").insert({
                            "company_id": active_co_id, "vouch_no": "AUTO", "vouch_type": v_type,
                            "date": str(v_date), "total_amount": amt, "narration": nar
                        }).execute()
                        v_id = v_head.data[0]['id']
                        
                        # 2. Insert Split Entries (Double Entry)
                        supabase.table("voucher_entries").insert([
                            {"voucher_id": v_id, "ledger_id": dr_id, "debit_amount": amt},
                            {"voucher_id": v_id, "ledger_id": cr_id, "credit_amount": amt}
                        ]).execute()
                        st.success("Posted to Eternal Ledger.")

    # --- MODULE 4: FINAL ACCOUNTS (P&L / BS) ---
    elif choice == "⚖️ Final Accounts (P&L/BS)":
        st.header("Financial Performance")
                if active_co_id:
            # Relational Join to get amounts and ledger names
            res = supabase.table("voucher_entries").select("*, ledgers(name, company_id)").execute()
            ent_df = pd.json_normalize(res.data)
            
            # Filter for active company in Python logic for safety
            if not ent_df.empty:
                ent_df = ent_df[ent_df['ledgers.company_id'] == active_co_id]
                st.dataframe(ent_df[['ledgers.name', 'debit_amount', 'credit_amount']])
            else: st.info("No data.")

    # --- MODULE 5: FORENSIC AUDIT ---
    elif choice == "🛡️ Forensic Integrity Audit":
        st.header("Fraud & Integrity Scanner")
        if active_co_id:
            v_res = supabase.table("vouchers").select("*").eq("company_id", active_co_id).execute()
            v_df = pd.DataFrame(v_res.data)
            if not v_df.empty:
                dupes = v_df[v_df.duplicated(['total_amount', 'date'])]
                if not dupes.empty: st.warning(f"Suspected Duplicates: {len(dupes)}")
                else: st.success("Voucher Integrity: Verified.")

    if st.sidebar.button("🔐 LOGOUT"):
        st.session_state.logged_in = False; st.rerun()
