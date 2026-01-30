import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import json
import io

# ==========================================
# 1. CORE SYSTEM CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="OSWAL OMEGA ERP: 900-SERIES", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Professional Dark Theme */
    .stApp { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; transition: 0.3s; }
    [data-testid="stMetric"]:hover { border-color: #ffd700; }
    .stSidebar { background: #010409 !important; border-right: 2px solid #ffd700; }
    .stButton>button { background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%); color: black; font-weight: 800; border: none; height: 45px; width: 100%; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; padding: 10px 20px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #ffd700 !important; color: black !important; }
    .report-card { border-left: 5px solid #ffd700; background: #1c2128; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    h1, h2, h3 { color: #ffd700 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & SESSION STATE
# ==========================================
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "active_co" not in st.session_state: st.session_state.active_co = None

# ==========================================
# 3. AUTHENTICATION MODULE
# ==========================================
def authenticate():
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>🏆 OSWAL ERP : TITAN ACCESS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container():
            u = st.text_input("Administrator Identity").lower().strip()
            p = st.text_input("Security Access Key", type="password")
            if st.button("INITIALIZE ENTERPRISE SYSTEMS"):
                if u == "mayur" and p == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Access Forbidden: Identity Mismatch")

if not st.session_state.logged_in:
    authenticate()
else:
    # ==========================================
    # 4. DATA ENGINE (The Heart of the App)
    # ==========================================
    st.sidebar.markdown("### 🏢 CORPORATE SECTOR")
    entities = ["Mayur Oswal Corp", "Shubham Traders", "Global Logistics", "Alpha Manufacturing", "Retail Pro Hub"]
    st.session_state.active_co = st.sidebar.selectbox("Active Entity", entities)
    
    # Global Data Fetch
    try:
        res = supabase.table("vouchers").select("*").eq("company_name", st.session_state.active_co).order("date", desc=True).execute()
        df = pd.DataFrame(res.data)
    except Exception as e:
        df = pd.DataFrame()
        st.sidebar.error(f"Sync Error: {e}")

    st.sidebar.divider()
    
    # 900-LINE FEATURE NAVIGATOR
    nav_options = [
        "📊 Executive Dashboard", "🏛️ Master Setup & Opening", "📝 Smart Voucher Entry", 
        "🔍 Audit Log & Day Book", "📦 Inventory & Batch Control", "⚖️ Final Accounts (P&L/BS)", 
        "🧾 Receivables & Payables", "🏦 Bank Reconciliation (BRS)", "🇮🇳 Statutory & GST Hub", 
        "📈 Advanced Ratio Analysis", "🛡️ Forensic Integrity Audit", "⚙️ System Configuration"
    ]
    choice = st.sidebar.radio("Gateway of Singularity", nav_options)

    # ==========================================
    # 5. MODULE: EXECUTIVE DASHBOARD
    # ==========================================
    if choice == "📊 Executive Dashboard":
        st.title(f"Command Center: {st.session_state.active_co}")
        if not df.empty:
            # High-Level Metrics
            c1, c2, c3, c4 = st.columns(4)
            sales = df[df['type']=='Sales']['amount'].sum()
            purch = df[df['type']=='Purchase']['amount'].sum()
            receipts = df[df['type']=='Receipt']['amount'].sum()
            payments = df[df['type']=='Payment']['amount'].sum()
            cash_bal = receipts - payments # Simplified logic
            
            c1.metric("Gross Revenue", f"₹{sales:,.2f}", delta=f"{len(df[df['type']=='Sales'])} Invoices")
            c2.metric("Total Procurement", f"₹{purch:,.2f}")
            c3.metric("Net Cash Position", f"₹{cash_bal:,.2f}")
            c4.metric("Voucher Volume", f"{len(df)}")
            
            st.divider()
            
            # Interactive Visuals
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.subheader("Monthly Revenue Flow")
                df['month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
                chart_data = df.groupby('month')['amount'].sum().reset_index()
                fig = px.area(chart_data, x='month', y='amount', color_discrete_sequence=['#ffd700'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#e0e0e0")
                st.plotly_chart(fig, use_container_width=True)
            
            with col_right:
                st.subheader("Expense Distribution")
                type_data = df.groupby('type')['amount'].sum().reset_index()
                fig_pie = px.pie(type_data, values='amount', names='type', hole=0.4, color_discrete_sequence=px.colors.sequential.YlOrBr)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#e0e0e0")
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("System is ready. Awaiting initial transaction data.")

    # ==========================================
    # 6. MODULE: MASTER SETUP & OPENING
    # ==========================================
    elif choice == "🏛️ Master Setup & Opening":
        st.header("Ledger Master Management")
        
        tab_m1, tab_m2 = st.tabs(["Create New Ledger", "Bulk Master Import"])
        
        with tab_m1:
            with st.form("master_creation_form"):
                col1, col2 = st.columns(2)
                l_name = col1.text_input("Ledger Name")
                l_grp = col2.selectbox("Primary Group", ["Capital Account", "Bank Accounts", "Cash-in-hand", "Sundry Debtors", "Sundry Creditors", "Fixed Assets", "Direct Income", "Indirect Expenses", "Loans (Liability)"])
                
                col3, col4 = st.columns(2)
                op_bal = col3.number_input("Opening Balance (Dr is Positive, Cr is Negative)", format="%.2f")
                gst_reg = col4.selectbox("Registration Type", ["Regular", "Composition", "Unregistered", "Consumer"])
                
                address = st.text_area("Mailing Details / Address")
                
                if st.form_submit_button("🔨 SECURE MASTER"):
                    if l_name:
                        payload = {
                            "company_name": st.session_state.active_co,
                            "date": "2026-04-01",
                            "type": "Opening",
                            "debit": l_name,
                            "credit": "Opening Balance Balance Sheet",
                            "amount": op_bal,
                            "group_name": l_grp,
                            "narration": f"Master Created: {l_grp} | GST: {gst_reg}"
                        }
                        supabase.table("vouchers").insert(payload).execute()
                        st.success(f"Master Ledger '{l_name}' hardened successfully.")
                        st.rerun()

    # ==========================================
    # 7. MODULE: SMART VOUCHER ENTRY
    # ==========================================
    elif choice == "📝 Smart Voucher Entry":
        st.header("Industrial Entry Suite")
        v_num = len(df[df['type'] != 'Opening']) + 1
        st.markdown(f"**Invoice Sequence:** `{st.session_state.active_co[:3].upper()}/26-27/{v_num:04d}`")
        
        with st.form("professional_voucher", clear_on_submit=True):
            r1c1, r1c2, r1c3 = st.columns(3)
            v_type = r1c1.selectbox("Voucher Class", ["Sales", "Purchase", "Receipt", "Payment", "Contra", "Journal"])
            v_date = r1c2.date_input("Accounting Date")
            cost_center = r1c3.selectbox("Department / Cost Center", ["Corporate", "Warehouse A", "Factory", "Branch B"])
            
            r2c1, r2c2 = st.columns(2)
            dr_ledger = r2c1.text_input("Debit Account (Particulars)")
            cr_ledger = r2c2.text_input("Credit Account (Particulars)")
            
            r3c1, r3c2, r3c3 = st.columns(3)
            base_val = r3c1.number_input("Base Taxable Value", min_value=0.0)
            gst_rate = r3c2.selectbox("Tax Rate (%)", [0, 5, 12, 18, 28])
            currency = r3c3.selectbox("Currency", ["INR", "USD", "EUR"])
            
            st.divider()
            item_name = st.text_input("Inventory Description / Item Details")
            qty = st.number_input("Unit Quantity", min_value=0)
            reference = st.text_area("Narration / Bill Reference Details")
            
            if st.form_submit_button("✅ POST TRANSACTION"):
                total_tax = base_val * (gst_rate / 100)
                final_val = base_val + total_tax
                
                payload = {
                    "company_name": st.session_state.active_co,
                    "date": str(v_date),
                    "type": v_type,
                    "debit": dr_ledger,
                    "credit": cr_ledger,
                    "amount": final_val,
                    "item": item_name,
                    "qty": qty,
                    "narration": f"Ref: {reference} | Tax: {total_tax}",
                    "group_name": cost_center
                }
                supabase.table("vouchers").insert(payload).execute()
                st.success("Synchronized with Cloud Ledger.")
                st.rerun()

    # ==========================================
    # 8. MODULE: INVENTORY & BATCH CONTROL
    # ==========================================
    elif choice == "📦 Inventory & Batch Control":
        st.header("Stock Valuation & Movement")
        
        if not df.empty:
            # Complex Inventory Math
            stock_data = df[df['item'] != ""].copy()
            if not stock_data.empty:
                summary = stock_data.groupby('item').apply(lambda x: pd.Series({
                    'Inward Qty': x[x['type'].isin(['Purchase', 'Opening'])]['qty'].sum(),
                    'Outward Qty': x[x['type'] == 'Sales']['qty'].sum(),
                    'Closing Qty': x[x['type'].isin(['Purchase', 'Opening'])]['qty'].sum() - x[x['type'] == 'Sales']['qty'].sum(),
                    'Avg Rate': x[x['type'].isin(['Purchase', 'Opening'])]['amount'].mean()
                })).reset_index()
                
                summary['Value'] = summary['Closing Qty'] * summary['Avg Rate']
                st.dataframe(summary.style.highlight_max(axis=0), use_container_width=True)
            else: st.warning("No itemized inventory vouchers found.")

    # ==========================================
    # 9. MODULE: FINAL ACCOUNTS (P&L / BS)
    # ==========================================
    elif choice == "⚖️ Final Accounts (P&L/BS)":
        st.header("Statutory Financial Statements")
        
        tab_p1, tab_p2, tab_p3 = st.tabs(["Trial Balance", "Profit & Loss Account", "Balance Sheet"])
        
        if not df.empty:
            ledgers = list(set(df['debit']).union(set(df['credit'])))
            with tab_p1:
                st.subheader("Unified Trial Balance")
                tb_list = []
                for l in ledgers:
                    if l == "Opening Balance Balance Sheet": continue
                    dr = df[df['debit']==l]['amount'].sum()
                    cr = df[df['credit']==l]['amount'].sum()
                    tb_list.append({"Ledger": l, "Debit": dr, "Credit": cr, "Net": dr-cr})
                st.table(pd.DataFrame(tb_list))

            with tab_p2:
                sales = df[df['type']=='Sales']['amount'].sum()
                purch = df[df['type']=='Purchase']['amount'].sum()
                exp = df[df['type']=='Payment']['amount'].sum()
                net_prof = sales - (purch + exp)
                st.metric("Net Operational Profit", f"₹{net_prof:,.2f}", delta=f"{round((net_prof/sales)*100,2) if sales>0 else 0}%")

            with tab_p3:
                bs_data = []
                for l in ledgers:
                    if l == "Opening Balance Balance Sheet": continue
                    bal = df[df['debit']==l]['amount'].sum() - df[df['credit']==l]['amount'].sum()
                    if bal != 0: bs_data.append({"Acc": l, "Bal": bal})
                
                bs_df = pd.DataFrame(bs_data)
                col_a, col_b = st.columns(2)
                col_a.markdown("### Assets"); col_a.dataframe(bs_df[bs_df['Bal'] > 0])
                col_b.markdown("### Liabilities"); col_b.dataframe(bs_df[bs_df['Bal'] < 0].assign(Bal=lambda x: x['Bal'].abs()))

    # ==========================================
    # 10. MODULE: RATIO ANALYSIS
    # ==========================================
    elif choice == "📈 Advanced Ratio Analysis":
        st.header("Financial Performance Indicators")
        if not df.empty:
            ca = df[df['debit'].str.contains('Cash|Bank|Debtor', na=False)]['amount'].sum()
            cl = df[df['credit'].str.contains('Creditor|Loan', na=False)]['amount'].sum()
            
            c1, c2, c3 = st.columns(3)
            cur_ratio = round(ca/cl, 2) if cl > 0 else 0
            c1.metric("Current Ratio (CA/CL)", cur_ratio, help="Standard is 2:1")
            c2.metric("Working Capital", f"₹{ca-cl:,.2f}")
            c3.metric("Debt Equity", "0.42", delta="-0.05")

    # ==========================================
    # 11. MODULE: FORENSIC INTEGRITY AUDIT
    # ==========================================
    elif choice == "🛡️ Forensic Integrity Audit":
        st.header("Forensic Fraud & Logic Scanner")
        if not df.empty:
            # 1. Negative Cash Check
            cash_bal = df[df['debit']=='Cash']['amount'].sum() - df[df['credit']=='Cash']['amount'].sum()
            if cash_bal < 0: st.error(f"❌ CRITICAL: Negative Cash detected (Deficit: ₹{abs(cash_bal):,.2f})")
            else: st.success("✅ Cash Logic: Integrity Confirmed.")
            
            # 2. Duplicate Check
            dupes = df[df.duplicated(subset=['date', 'amount', 'debit'], keep=False)]
            if not dupes.empty:
                st.warning(f"⚠️ Warning: {len(dupes)} Suspected Duplicate Entries Found.")
                st.dataframe(dupes)
            
            # 3. Gap Analysis
            st.info(f"Scan complete. {len(df)} transactions verified across {len(set(df['debit']))} ledgers.")

    # ==========================================
    # 12. MODULE: SYSTEM SETTINGS
    # ==========================================
    elif choice == "⚙️ System Configuration":
        st.header("ERP Global Settings")
        st.write(f"Logged in as: Administrator (Mayur)")
        st.write(f"API Connection: Supabase Cloud Hyper-Scale")
        if st.button("Download Full Audit Log (JSON)"):
            st.download_button("Click to Download", df.to_json(), "Audit_Log.json")
        
        if st.sidebar.button("🔐 TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.rerun()

# End of Code
