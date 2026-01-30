import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# 1. CORE SYSTEM CONFIG
st.set_page_config(page_title="OSWAL TALLY ERP: ULTIMATE", layout="wide")

# 2. DATABASE AUTH
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 3. SESSION STATE FOR "PURE" APP FEEL
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 4. LOGIN INTERFACE
if not st.session_state.logged_in:
    st.title("🛡️ Enterprise Secure Gateway")
    with st.container():
        u = st.text_input("Username").lower().strip()
        p = st.text_input("Password", type="password")
        if st.button("Access System"):
            if u == "mayur" and p == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
else:
    # 5. DATA ENGINE: FETCHING ALL TABLES
    try:
        v_res = supabase.table("vouchers").select("*").execute()
        df = pd.DataFrame(v_res.data)
    except:
        df = pd.DataFrame()

    # SIDEBAR: THE GATEWAY OF TALLY
    st.sidebar.title("🚩 Gateway of Tally")
    menu = ["📊 Dashboard", "📝 Voucher Entry", "📦 Inventory Master", "📖 Day Book", "⚖️ Trial Balance", "📈 Profit & Loss", "🏦 Balance Sheet"]
    choice = st.sidebar.radio("Main Menu", menu)

    # --- DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("Business Analytics")
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Sales", f"₹{df[df['type']=='Sales']['amount'].sum():,.2f}")
            c2.metric("Total Purchases", f"₹{df[df['type']=='Purchase']['amount'].sum():,.2f}")
            c3.metric("Net Cash Flow", f"₹{df['amount'].sum():,.2f}")
            st.area_chart(df.groupby('date')['amount'].sum())
        else:
            st.info("System Ready. Please enter initial vouchers.")

    # --- VOUCHER ENTRY (Double Entry Logic) ---
    elif choice == "📝 Voucher Entry":
        st.header("Voucher Creation (Double Entry)")
        with st.form("v_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            v_type = col1.selectbox("Voucher Type", ["Receipt", "Payment", "Contra", "Sales", "Purchase", "Journal"])
            v_date = col2.date_input("Date")
            
            dr_ledger = st.text_input("Particulars (Debit Account)")
            cr_ledger = st.text_input("Particulars (Credit Account)")
            
            col3, col4 = st.columns(2)
            v_amt = col3.number_input("Amount (₹)", min_value=0.0)
            v_item = col4.text_input("Item Name (For Inventory)")
            
            v_narration = st.text_area("Narration")
            
            if st.form_submit_button("Accept"):
                if dr_ledger and cr_ledger and v_amt > 0:
                    payload = {
                        "date": str(v_date), "type": v_type, "debit": dr_ledger,
                        "credit": cr_ledger, "amount": v_amt, "item": v_item, "narration": v_narration
                    }
                    supabase.table("vouchers").insert(payload).execute()
                    st.success("Voucher Posted Successfully!")
                    st.rerun()

    # --- DAY BOOK ---
    elif choice == "📖 Day Book":
        st.header("Day Book")
        if not df.empty:
            st.dataframe(df[['date', 'type', 'debit', 'credit', 'amount', 'narration']], use_container_width=True)
        else:
            st.warning("No entries found.")

    # --- TRIAL BALANCE ---
    elif choice == "⚖️ Trial Balance":
        st.header("Trial Balance")
        if not df.empty:
            all_ledgers = set(df['debit']).union(set(df['credit']))
            tb_list = []
            for led in all_ledgers:
                dr = df[df['debit'] == led]['amount'].sum()
                cr = df[df['credit'] == led]['amount'].sum()
                tb_list.append({"Ledger": led, "Debit": dr if dr > cr else 0, "Credit": cr if cr > dr else 0})
            st.table(pd.DataFrame(tb_list))

    # --- BALANCE SHEET (The "Pure" Logic) ---
    elif choice == "🏦 Balance Sheet":
        st.header("Balance Sheet")
        if not df.empty:
            all_ledgers = set(df['debit']).union(set(df['credit']))
            balances = []
            for led in all_ledgers:
                bal = df[df['debit'] == led]['amount'].sum() - df[df['credit'] == led]['amount'].sum()
                balances.append({"Ledger": led, "Balance": bal})
            
            b_df = pd.DataFrame(balances)
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Liabilities")
                st.table(b_df[b_df['Balance'] < 0])
            with c2:
                st.subheader("Assets")
                st.table(b_df[b_df['Balance'] > 0])

    # --- INVENTORY MASTER ---
    elif choice == "📦 Inventory Master":
        st.header("Stock Summary")
        if not df.empty and 'item' in df.columns:
            items = df[df['item'] != ""].groupby('item').agg({
                'amount': 'count'
            }).rename(columns={'amount': 'Quantity Sold/Purchased'})
            st.table(items)
        else:
            st.info("No inventory movements recorded.")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
