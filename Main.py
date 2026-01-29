import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# 1. PAGE SETUP
st.set_page_config(page_title="MAYUR OSWAL TALLY ERP", page_icon="🏦", layout="wide")

# 2. CLOUD DATABASE
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 3. AUTHENTICATION LOGIC
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛡️ Gateway to Tally: Secure Login")
    u_input = st.text_input("Username").lower().strip()
    p_input = st.text_input("Password", type="password").strip()
    
    if st.button("Login"):
        # This checks for 'mayur' and '1234' while ignoring spaces/capitals
        if u_input == "mayur" and p_input == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Access Denied: Use username 'mayur' and password '1234'")
else:
    # 4. GATEWAY OF TALLY NAVIGATION
    st.sidebar.title("🚩 Gateway of Tally")
    menu = [
        "Dashboard", "Voucher Entry (F4-F9)", "Day Book", 
        "Trial Balance", "Profit & Loss A/c", "Balance Sheet", 
        "Stock Summary", "Export to Desktop"
    ]
    choice = st.sidebar.radio("Main Menu", menu)
    
    # FETCH DATA
    try:
        res = supabase.table("vouchers").select("*").execute()
        df = pd.DataFrame(res.data)
    except:
        df = pd.DataFrame()

    if choice == "Dashboard":
        st.title("📊 Accounting Dashboard")
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.metric("Total Vouchers", len(df))
            c2.metric("Total Value", f"₹{df['amount'].sum():,.2f}")
            st.line_chart(df.groupby('date')['amount'].sum())
        else:
            st.info("No data yet. Go to Voucher Entry.")

    elif choice == "Voucher Entry (F4-F9)":
        st.header("📝 Voucher Creation")
        v_type = st.selectbox("Type", ["Payment", "Receipt", "Contra", "Journal", "Sales", "Purchase"])
        with st.form("tally_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                v_date = st.date_input("Date")
                dr = st.text_input("By (Debit)")
            with col2:
                amt = st.number_input("Amount", min_value=0.0)
                cr = st.text_input("To (Credit)")
            nar = st.text_area("Narration")
            if st.form_submit_button("Accept"):
                if dr and cr and amt > 0:
                    data = {"date": str(v_date), "type": v_type, "debit": dr, "credit": cr, "amount": amt, "narration": nar}
                    supabase.table("vouchers").insert(data).execute()
                    st.success("Voucher Saved!")
                else:
                    st.error("Please fill all fields.")

    elif choice == "Trial Balance":
        st.header("⚖️ Trial Balance")
        if not df.empty:
            d_sum = df.groupby('debit')['amount'].sum()
            c_sum = df.groupby('credit')['amount'].sum()
            all_ac = sorted(list(set(d_sum.index) | set(c_sum.index)))
            st.table([{"Particulars": a, "Debit": d_sum.get(a,0), "Credit": c_sum.get(a,0)} for a in all_ac])

    elif choice == "Profit & Loss A/c":
        st.header("📈 Profit & Loss")
        if not df.empty:
            sales = df[df['type'] == 'Sales']['amount'].sum()
            pur = df[df['type'] == 'Purchase']['amount'].sum()
            st.metric("Gross Profit", f"₹{sales - pur}")

    elif choice == "Export to Desktop":
        st.header("📤 Export Data")
        if not df.empty:
            st.download_button("Download CSV for Tally Prime", df.to_csv(index=False), "tally.csv", "text/csv")

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
