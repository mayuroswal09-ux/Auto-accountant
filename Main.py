import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px

# 1. SYSTEM CONFIGURATION
st.set_page_config(page_title="OSWAL TALLY PRO: ENTERPRISE", layout="wide", initial_sidebar_state="expanded")

# 2. CLOUD DATABASE ENGINE
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 3. AUTHENTICATION ENGINE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.markdown("<h1 style='text-align: center;'>🔐 ENTERPRISE GATEWAY</h1>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            u = st.text_input("Admin ID").lower().strip()
            p = st.text_input("Access Key", type="password")
            if st.button("AUTHENTICATE", use_container_width=True):
                if u == "mayur" and p == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

# 4. DATA PROCESSING CORE
def fetch_all_data():
    try:
        res = supabase.table("vouchers").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

# 5. MAIN APPLICATION LOGIC
if not st.session_state.logged_in:
    login_screen()
else:
    df = fetch_all_data()
    
    # SIDEBAR NAVIGATION
    st.sidebar.title("💎 OSWAL TALLY PRO")
    st.sidebar.info(f"Connected to Cloud: {datetime.now().strftime('%Y-%m-%d')}")
    
    menu = ["📊 Executive Dashboard", "📝 Voucher Management", "📖 Digital Day Book", 
            "⚖️ Trial Balance", "📊 Profit & Loss", "🏦 Balance Sheet", "⚙️ System Settings"]
    choice = st.sidebar.radio("Main Menu", menu)

    # --- DASHBOARD MODULE ---
    if choice == "📊 Executive Dashboard":
        st.title("Financial Overview")
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            total_val = df['amount'].sum()
            c1.metric("Gross Turnover", f"₹{total_val:,.2f}")
            c2.metric("Total Vouchers", len(df))
            
            # Interactive Chart
            fig = px.area(df, x="created_at", y="amount", title="Cash Flow Velocity")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data found in cloud database.")

    # --- VOUCHER ENTRY MODULE ---
    elif choice == "📝 Voucher Management":
        st.header("Advanced Voucher Creation")
        tabs = st.tabs(["New Entry", "Pending Approvals", "Drafts"])
        
        with tabs[0]:
            with st.form("pro_entry", clear_on_submit=True):
                c1, c2 = st.columns(2)
                v_type = c1.selectbox("Voucher Category", ["Payment", "Receipt", "Contra", "Sales", "Purchase", "Journal"])
                v_date = c2.date_input("Accounting Date")
                
                dr_acc = st.text_input("Debit Account (Dr)")
                cr_acc = st.text_input("Credit Account (Cr)")
                
                c3, c4 = st.columns(2)
                amt = c3.number_input("Transaction Value (INR)", min_value=0.01)
                gst = c4.selectbox("GST Rate (%)", [0, 5, 12, 18, 28])
                
                narration = st.text_area("Narration / Remarks")
                
                if st.form_submit_button("✅ POST TO CLOUD"):
                    if dr_acc and cr_acc and amt > 0:
                        payload = {
                            "debit": dr_acc, "credit": cr_acc, "amount": amt,
                            "type": v_type, "narration": narration, "date": str(v_date)
                        }
                        supabase.table("vouchers").insert(payload).execute()
                        st.success("Transaction Successfully Hardened to Database.")
                        st.rerun()

    # --- DAY BOOK MODULE ---
    elif choice == "📖 Digital Day Book":
        st.header("Transaction Logs")
        if not df.empty:
            # Filtering logic
            search = st.text_input("🔍 Search by Account Name")
            filtered_df = df[(df['debit'].str.contains(search, case=False)) | (df['credit'].str.contains(search, case=False))]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.error("Log file is empty.")

    # --- BALANCE SHEET MODULE ---
    elif choice == "🏦 Balance Sheet":
        st.header("Institutional Balance Sheet")
        if not df.empty:
            # Calculate Net Balances
            all_accounts = set(df['debit']).union(set(df['credit']))
            balances = []
            for acc in all_accounts:
                dr_val = df[df['debit'] == acc]['amount'].sum()
                cr_val = df[df['credit'] == acc]['amount'].sum()
                balances.append({"Particulars": acc, "Net": dr_val - cr_val})
            
            b_df = pd.DataFrame(balances)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Liabilities (Sources)")
                st.table(b_df[b_df['Net'] < 0].assign(Net=lambda x: x['Net'].abs()))
                
            with col2:
                st.subheader("Assets (Applications)")
                st.table(b_df[b_df['Net'] > 0])
        else:
            st.info("Insufficient data for balance calculation.")

    # LOGOUT
    if st.sidebar.button("EXIT SYSTEM"):
        st.session_state.logged_in = False
        st.rerun()
