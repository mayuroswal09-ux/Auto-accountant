import streamlit as st
import pandas as pd
import sqlite3
import datetime
import pytesseract
import requests
from PIL import Image

# --- THEME & CONFIG ---
st.set_page_config(page_title="TallyFlow Ultra ERP", layout="wide")
st.markdown("<style>.main {background-color: #f0f2f6;}</style>", unsafe_allow_html=True)

class UltraERP:
    def __init__(self):
        self.conn = sqlite3.connect("tally_ultra.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._boot_system()

    def _boot_system(self):
        # 1. Accounts & Vouchers
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ledgers (name TEXT PRIMARY KEY, group_name TEXT, balance REAL DEFAULT 0)')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS vouchers (id INTEGER PRIMARY KEY, date TEXT, type TEXT, 
                               dr TEXT, cr TEXT, amount REAL, gst REAL, total REAL, narr TEXT, status TEXT)''')
        
        # 2. Inventory (Stock)
        self.cursor.execute('CREATE TABLE IF NOT EXISTS items (name TEXT PRIMARY KEY, category TEXT, qty INTEGER, rate REAL)')
        
        # 3. Payroll (Staff)
        self.cursor.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT, salary REAL, attendance INTEGER DEFAULT 0)')
        
        # Seed default data
        if self.cursor.execute("SELECT COUNT(*) FROM ledgers").fetchone()[0] == 0:
            self.cursor.executemany("INSERT INTO ledgers VALUES (?,?,?)", 
                [('Cash', 'Asset', 0), ('HDFC Bank', 'Asset', 0), ('Sales', 'Income', 0), ('Purchase', 'Expense', 0), ('GST Payable', 'Liability', 0)])
        self.conn.commit()

# --- APP LOGIC ---
erp = UltraERP()

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 TallyFlow Ultra Login")
    u = st.text_input("User")
    p = st.text_input("Pass", type="password")
    if st.button("Access ERP"):
        if u == "admin" and p == "ultra99": 
            st.session_state.user = "Admin"
            st.rerun()
else:
    st.sidebar.title(f"🚀 ERP Dashboard")
    page = st.sidebar.selectbox("Go To", ["MIS Dashboard", "Inventory (Stock)", "Voucher Entry (GST)", "Payroll", "Trial Balance", "Balance Sheet", "Tally Sync"])

    # --- 1. MIS DASHBOARD ---
    if page == "MIS Dashboard":
        st.header("📊 Executive Summary")
        c1, c2, c3, c4 = st.columns(4)
        total_v = erp.cursor.execute("SELECT SUM(total) FROM vouchers").fetchone()[0] or 0
        stock_val = erp.cursor.execute("SELECT SUM(qty * rate) FROM items").fetchone()[0] or 0
        
        c1.metric("Total Revenue", f"₹{total_v:,.2f}")
        c2.metric("Stock Value", f"₹{stock_val:,.2f}")
        c3.metric("Cash Balance", "₹0.00") # Calculated dynamically in TB
        c4.metric("GST Liability", "₹0.00")
        
        st.subheader("Inventory Levels")
        items_df = pd.read_sql_query("SELECT name, qty FROM items", erp.conn)
        if not items_df.empty: st.bar_chart(items_df.set_index('name'))

    # --- 2. INVENTORY (STOCK) ---
    elif page == "Inventory (Stock)":
        st.header("📦 Inventory Management")
        with st.expander("Add New Item"):
            iname = st.text_input("Item Name")
            icat = st.selectbox("Category", ["Raw Material", "Finished Goods", "Trading"])
            iqty = st.number_input("Opening Qty", min_value=0)
            irate = st.number_input("Unit Rate", min_value=0.0)
            if st.button("Save Item"):
                erp.cursor.execute("INSERT OR REPLACE INTO items VALUES (?,?,?,?)", (iname, icat, iqty, irate))
                erp.conn.commit()
        
        st.subheader("Current Stock")
        st.dataframe(pd.read_sql_query("SELECT * FROM items", erp.conn), use_container_width=True)
        

    # --- 3. VOUCHER ENTRY (GST) ---
    elif page == "Voucher Entry (GST)":
        st.header("🧾 Smart Billing & GST")
        col1, col2 = st.columns(2)
        with col1:
            v_type = st.selectbox("Type", ["Sales", "Purchase", "Payment", "Receipt"])
            v_date = st.date_input("Date")
            v_amt = st.number_input("Taxable Value", min_value=0.0)
            v_gst_rate = st.selectbox("GST %", [0, 5, 12, 18, 28])
        
        gst_amt = (v_amt * v_gst_rate) / 100
        total_amt = v_amt + gst_amt
        
        with col2:
            st.info(f"GST: ₹{gst_amt:,.2f} | Net Total: ₹{total_amt:,.2f}")
            dr_led = st.selectbox("Debit Ledger", [n[0] for n in erp.cursor.execute("SELECT name FROM ledgers")])
            cr_led = st.selectbox("Credit Ledger", [n[0] for n in erp.cursor.execute("SELECT name FROM ledgers")])
            v_narr = st.text_input("Narration")
            
        if st.button("Post Transaction"):
            erp.cursor.execute("INSERT INTO vouchers (date, type, dr, cr, amount, gst, total, narr, status) VALUES (?,?,?,?,?,?,?,?,?)",
                              (str(v_date), v_type, dr_led, cr_led, v_amt, gst_amt, total_amt, v_narr, 'Approved'))
            erp.conn.commit()
            st.success("Transaction Posted to Ledger!")
        

    # --- 4. PAYROLL ---
    elif page == "Payroll":
        st.header("👥 Staff & Payroll")
        with st.form("staff"):
            sname = st.text_input("Employee Name")
            ssal = st.number_input("Monthly Salary", min_value=0.0)
            if st.form_submit_button("Add Employee"):
                erp.cursor.execute("INSERT INTO staff (name, salary) VALUES (?,?)", (sname, ssal))
                erp.conn.commit()
        
        st.subheader("Generate Monthly Pay")
        staff_df = pd.read_sql_query("SELECT * FROM staff", erp.conn)
        st.table(staff_df)

    # --- 5. FINANCIAL STATEMENTS ---
    elif page in ["Trial Balance", "Balance Sheet"]:
        st.header(f"🏛️ {page}")
        tb_query = """SELECT name, 
                      (SELECT TOTAL(total) FROM vouchers WHERE dr=name) as Debit,
                      (SELECT TOTAL(total) FROM vouchers WHERE cr=name) as Credit
                      FROM ledgers"""
        df_tb = pd.read_sql_query(tb_query, erp.conn)
        df_tb['Closing'] = df_tb['Debit'] - df_tb['Credit']
        st.table(df_tb)
        

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
