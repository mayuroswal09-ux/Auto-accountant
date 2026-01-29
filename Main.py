import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# 1. PREMIUM ERP CONFIGURATION
st.set_page_config(page_title="MAYUR OSWAL TALLY ERP - ULTIMATE", page_icon="🏦", layout="wide")

# 2. SECURE CLOUD DATABASE CONNECTION
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 3. GATEWAY SECURITY SYSTEM
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛡️ MAYUR OSWAL TALLY ERP: ULTIMATE EDITION")
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("Admin Username")
        pwd = st.text_input("Access Key (Password)", type="password")
        if st.button("Login to Gateway of Tally"):
                            if user == "mayur" and pwd == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Access Denied: Please check credentials")
            
else:
    # 4. FULL GATEWAY OF TALLY NAVIGATION
    st.sidebar.title("🚩 Gateway of Tally")
    menu = [
        "Dashboard (Control Center)", 
        "Voucher Entry (F4 to F10)", 
        "Day Book", 
        "Ledger Reports", 
        "Trial Balance", 
        "Profit & Loss A/c", 
        "Balance Sheet", 
        "Stock Summary (Inventory)",
        "Sync & Export to Desktop"
    ]
    choice = st.sidebar.radio("Main Menu", menu)
    
    # FETCH ALL CLOUD RECORDS
    try:
        res = supabase.table("vouchers").select("*").execute()
        df = pd.DataFrame(res.data)
    except:
        df = pd.DataFrame()

    # --- FEATURE: ANALYTICS DASHBOARD ---
    if choice == "Dashboard (Control Center)":
        st.title("📊 Real-Time Financial Overview")
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vouchers", len(df))
            c2.metric("Total Inflow", f"₹{df[df['type'].str.contains('Receipt|Sales')]['amount'].sum():,.2f}")
            c3.metric("Total Outflow", f"₹{df[df['type'].str.contains('Payment|Purchase')]['amount'].sum():,.2f}")
            c4.metric("Cash Balance", f"₹{df['amount'].sum():,.2f}")
            st.subheader("Transaction Trends")
            st.area_chart(df.groupby('date')['amount'].sum())
        else:
            st.warning("No data found. Record your first voucher to see analytics.")

    # --- FEATURE: FULL VOUCHER SUITE ---
    elif choice == "Voucher Entry (F4 to F10)":
        st.header("📝 Create Accounting Voucher")
        v_type = st.selectbox("Voucher Type", 
            ["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)", "Sales (F8)", "Purchase (F9)", "Debit Note (F10)", "Credit Note"])
        
        with st.form("tally_ultimate_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                v_date = st.date_input("Voucher Date")
                dr_ledger = st.text_input("Particulars (Dr / By)")
                v_no = st.text_input("Voucher No.", value=f"V-{len(df)+1 if not df.empty else 1}")
            with col_b:
                cr_ledger = st.text_input("Particulars (Cr / To)")
                amount = st.number_input("Amount (INR)", min_value=0.0, step=1.0)
                stock_item = st.text_input("Stock Item (Inventory Name)")
            
            narration = st.text_area("Narration")
            
            if st.form_submit_button("✅ Accept"):
                if dr_ledger and cr_ledger and amount > 0:
                    data = {
                        "date": str(v_date), "type": v_type, "v_no": v_no,
                        "debit": dr_ledger, "credit": cr_ledger, 
                        "amount": amount, "narration": narration, "item": stock_item
                    }
                    supabase.table("vouchers").insert(data).execute()
                    st.success(f"Voucher {v_no} Saved Successfully!")
                else:
                    st.error("Mandatory fields: Ledgers and Amount.")

    # --- FEATURE: FINANCIAL STATEMENTS ---
    elif choice == "Trial Balance":
        st.header("⚖️ Trial Balance")
        if not df.empty:
            dr = df.groupby('debit')['amount'].sum().rename("Debit")
            cr = df.groupby('credit')['amount'].sum().rename("Credit")
            tb = pd.concat([dr, cr], axis=1).fillna(0)
            st.dataframe(tb, use_container_width=True)

    elif choice == "Profit & Loss A/c":
        st.header("📈 Profit & Loss Account")
        if not df.empty:
            income = df[df['type'].str.contains("Sales|Receipt")]['amount'].sum()
            expense = df[df['type'].str.contains("Purchase|Payment")]['amount'].sum()
            st.metric("Total Revenue", f"₹{income}")
            st.metric("Total Expenses", f"₹{expense}")
            st.success(f"Net Profit: ₹{income - expense}")

    elif choice == "Balance Sheet":
        st.header("🏢 Balance Sheet")
        if not df.empty:
            st.subheader("Assets (Debit Balances)")
            st.write(df.groupby('debit')['amount'].sum())
            st.subheader("Liabilities (Credit Balances)")
            st.write(df.groupby('credit')['amount'].sum())

    # --- FEATURE: EXPORT ---
    elif choice == "Sync & Export to Desktop":
        st.header("📤 Sync with Desktop Tally")
        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download XML/CSV for Tally Prime", csv_data, "Tally_Sync.csv", "text/csv")

    st.sidebar.markdown("---")
    st.sidebar.button("F12: Quit / Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
