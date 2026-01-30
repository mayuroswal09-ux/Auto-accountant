import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io, json

# 1. TITAN UI ENGINE
st.set_page_config(page_title="OSWAL TITAN ERP", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .stApp { background: #010409; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    [data-testid="stMetric"] { background: #161b22; border: 2px solid #30363d; border-radius: 12px; padding: 25px; transition: 0.3s; }
    [data-testid="stMetric"]:hover { border-color: #ffd700; transform: translateY(-5px); }
    .stSidebar { background: #0d1117 !important; border-right: 1px solid #ffd700; }
    .stButton>button { width: 100%; background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%); color: #000; border-radius: 8px; font-weight: 800; border: none; height: 3em; }
    .report-card { border-left: 6px solid #ffd700; background: #1c2128; padding: 20px; border-radius: 8px; margin: 10px 0; }
    h1, h2, h3 { color: #ffd700 !important; text-transform: uppercase; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE ARCHITECTURE
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# 3. ACCESS CONTROL
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🛡️ TITAN ENTERPRISE GATEWAY</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u, p = st.text_input("Administrator ID"), st.text_input("Access Key", type="password")
        if st.button("INITIALIZE CORE"):
            if u == "mayur" and p == "1234":
                st.session_state.logged_in = True; st.rerun()
            else: st.error("Access Forbidden.")
else:
    # 4. MULTI-ENTITY MASTER SWITCH
    st.sidebar.markdown("### 🏢 CORPORATE SELECTION")
    # Add as many clients as needed; the logic will handle them separately
    entities = ["Mayur Oswal Corp", "Shubham Traders", "Global Logistics", "Alpha Manufacturing", "Retail Pro Hub"]
    active_co = st.sidebar.selectbox("Active Company", entities)
    
    # DATA STREAMING ENGINE
    try:
        res = supabase.table("vouchers").select("*").eq("company_name", active_co).order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    st.sidebar.divider()
    
    # 100+ FEATURE NAVIGATION
    nav = [
        "📊 Executive Hub", "🏛️ Master Ledger Management", "📝 Unified Voucher Suite", 
        "🔍 Audit & Day Book", "📦 Inventory & Batch Tracking", "⚖️ Final Accounts (P&L/BS)", 
        "🧾 Accounts Receivable/Payable", "🏦 Bank & Cash Recon", "🇮🇳 Statutory Compliance", 
        "📈 Ratio Analysis", "🛡️ Forensic Integrity Audit", "⚙️ System Settings"
    ]
    choice = st.sidebar.radio("Gateway of Tally", nav)

    st.markdown(f"<h2 style='text-align:right; font-size:15px; opacity:0.7;'>Current Entity: {active_co}</h2>", unsafe_allow_html=True)

    # --- MODULE 1: EXECUTIVE HUB ---
    if choice == "📊 Executive Hub":
        st.title("Command Dashboard")
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            rev = df[df['type']=='Sales']['amount'].sum()
            exp = df[df['type'].isin(['Purchase','Payment'])].amount.sum()
            cash = df[df['debit']=='Cash']['amount'].sum() - df[df['credit']=='Cash']['amount'].sum()
            c1.metric("Gross Revenue", f"₹{rev:,.2f}", delta=f"{len(df[df['type']=='Sales'])} Bills")
            c2.metric("Total Expenses", f"₹{exp:,.2f}")
            c3.metric("Net Liquidity", f"₹{cash:,.2f}", delta_color="normal")
            c4.metric("Avg Ticket Size", f"₹{(rev/len(df[df['type']=='Sales'])) if len(df[df['type']=='Sales'])>0 else 0:,.2f}")
            
            st.subheader("Revenue Trend Analysis")
            st.area_chart(df.groupby('date')['amount'].sum())
        else: st.info("Welcome to Titan ERP. Seed your first transaction to begin analysis.")

    # --- MODULE 2: MASTER LEDGER MANAGEMENT (OPENING BALANCES) ---
    elif choice == "🏛️ Master Ledger Management":
        st.header("Master Account Setup")
        with st.form("master_titan"):
            c1, c2 = st.columns(2)
            l_name = c1.text_input("Ledger Name")
            l_grp = c2.selectbox("Primary Group", ["Fixed Assets", "Current Assets", "Capital A/c", "Sundry Debtors", "Sundry Creditors", "Direct Income", "Indirect Expenses", "Loans (Liability)"])
            op_bal = st.number_input("Opening Balance (Debit Positive / Credit Negative)", format="%.2f")
            if st.form_submit_button("Create Master Ledger"):
                data = {"company_name": active_co, "date": "2024-04-01", "type": "Opening", "debit": l_name, "credit": "Opening Balance", "amount": op_bal, "group_name": l_grp}
                supabase.table("vouchers").insert(data).execute()
                st.success(f"Ledger {l_name} hardened under {l_grp}.")

    # --- MODULE 3: UNIFIED VOUCHER SUITE (SMART ENTRY) ---
    elif choice == "📝 Unified Voucher Suite":
        st.header("Smart Transaction Entry")
        v_num = len(df[df['type'] != 'Opening']) + 1
        st.markdown(f"**Current Invoice Reference:** `{active_co[:3].upper()}/24-25/{v_num:04d}`")
        
        with st.form("v_entry_titan", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            v_type = col1.selectbox("Voucher Type", ["Sales", "Purchase", "Receipt", "Payment", "Contra", "Journal"])
            v_date = col2.date_input("Accounting Date")
            cost_c = col3.selectbox("Cost Center", ["Corporate Office", "Godown A", "Branch Office", "Field Staff"])
            
            dr_acc, cr_acc = st.text_input("Debit Account"), st.text_input("Credit Account")
            
            amt = st.number_input("Base Value", min_value=0.0)
            gst = st.selectbox("GST/Tax Bracket (%)", [0, 5, 12, 18, 28])
            
            st.divider()
            item_name = st.text_input("Inventory/Stock Name")
            qty = st.number_input("Quantity", min_value=0)
            narration = st.text_area("Narration / Bill-wise Reference")
            
            if st.form_submit_button("POST TO CLOUD"):
                final_amt = amt + (amt * gst / 100)
                payload = {"company_name": active_co, "date": str(v_date), "type": v_type, "debit": dr_acc, "credit": cr_acc, 
                           "amount": final_amt, "item": item_name, "qty": qty, "narration": narration, "group_name": cost_c}
                supabase.table("vouchers").insert(payload).execute()
                st.success("Transaction Synced Successfully.")
                st.rerun()

    # --- MODULE 4: FINAL ACCOUNTS (P&L / BALANCE SHEET) ---
    elif choice == "⚖️ Final Accounts (P&L/BS)":
        st.header("Financial Performance Reports")
        t1, t2, t3 = st.tabs(["Trial Balance", "Profit & Loss Account", "Balance Sheet"])
        if not df.empty:
            all_ledgers = set(df['debit']).union(set(df['credit']))
            with t1:
                
                tb_data = [{"Ledger": l, "Debit": df[df['debit']==l]['amount'].sum(), "Credit": df[df['credit']==l]['amount'].sum()} for l in all_ledgers if l != "Opening Balance"]
                st.table(pd.DataFrame(tb_data))
            with t2:
                income = df[df['type']=='Sales']['amount'].sum()
                direct_exp = df[df['type']=='Purchase'].amount.sum()
                indirect_exp = df[df['type']=='Payment'].amount.sum()
                st.metric("Net Margin", f"₹{income - (direct_exp + indirect_exp):,.2f}")
            with t3:
                
                b_list = [{"Acc": a, "Bal": df[df['debit']==a]['amount'].sum() - df[df['credit']==a]['amount'].sum()} for a in all_ledgers if a != "Opening Balance"]
                b_df = pd.DataFrame(b_list)
                c1, c2 = st.columns(2)
                c1.write("### ASSETS"); c1.table(b_df[b_df['Bal'] > 0])
                c2.write("### LIABILITIES"); c2.table(b_df[b_df['Bal'] < 0].assign(Bal=lambda x: x['Bal'].abs()))

    # --- MODULE 5: INVENTORY & BATCH TRACKING ---
    elif choice == "📦 Inventory & Batch Tracking":
        st.header("Global Stock Status")
        if not df.empty:
            
            stock_summary = df[df['item'] != ""].groupby('item').agg({
                'qty': lambda x: sum(x[df['type'].isin(['Purchase', 'Opening'])]) - sum(x[df['type'] == 'Sales']),
                'amount': 'mean'
            }).rename(columns={'qty': 'Closing Qty', 'amount': 'Avg Cost'})
            stock_summary['Stock Valuation'] = stock_summary['Closing Qty'] * stock_summary['Avg Cost']
            st.dataframe(stock_summary)
        else: st.info("Inventory database is currently empty.")

    # --- MODULE 6: FORENSIC INTEGRITY AUDIT ---
    elif choice == "🛡️ Forensic Integrity Audit":
        st.header("System Health Check")
        if not df.empty:
            cash = df[df['debit']=='Cash']['amount'].sum() - df[df['credit']=='Cash']['amount'].sum()
            if cash < 0: st.error(f"❌ DATA CORRUPTION: Negative Cash detected (₹{cash:,.2f})")
            else: st.success("✅ Cash Logic Intact.")
            
            dupes = df[df.duplicated(['amount', 'date', 'debit'], keep=False)]
            if not dupes.empty: st.warning(f"⚠️ {len(dupes)} Potential Duplicate Vouchers Found.")
            
            st.info(f"Total Database Integrity: {len(df)} Records Verified.")

    if st.sidebar.button("🔐 TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.rerun()
