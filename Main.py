import streamlit as st
import pandas as pd
import sqlite3
import datetime
import pytesseract
import re
from PIL import Image

# --- THE SMART ENGINE ---
class UltimateAccountingSystem:
    def __init__(self, db_name="ultimate_ledger.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()
        self.mappings = {
            "amazon": "Office Supplies",
            "airtel": "Telephone Expense",
            "jio": "Internet Expense",
            "uber": "Conveyance",
            "zomato": "Staff Welfare",
            "shell": "Fuel & Oil",
            "starbucks": "Refreshments"
        }

    def _init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, particulars TEXT, vch_type TEXT,
            dr_ledger TEXT, cr_ledger TEXT, 
            base_amt REAL, cgst REAL, sgst REAL, total REAL,
            is_deleted INTEGER DEFAULT 0
        )''')
        self.conn.commit()

    def auto_map_ledger(self, text):
        """AI-lite logic to guess the ledger based on keywords"""
        text = text.lower()
        for key, ledger in self.mappings.items():
            if key in text:
                return ledger
        return "General Expense"

    def calculate_gst(self, total, rate=18):
        base = round(total / (1 + (rate / 100)), 2)
        gst = round((total - base) / 2, 2)
        return base, gst, gst

    def post_entry(self, date, vendor, dr, cr, total, tax_rate=18):
        base, cgst, sgst = self.calculate_gst(total, tax_rate)
        self.cursor.execute('''INSERT INTO transactions 
            (date, particulars, vch_type, dr_ledger, cr_ledger, base_amt, cgst, sgst, total)
            VALUES (?,?,?,?,?,?,?,?,?)''', 
            (date, vendor, "Payment", dr, cr, base, cgst, sgst, total))
        self.conn.commit()

    def generate_xml(self, df):
        xml = '<ENVELOPE>\n<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>\n<BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>\n'
        for _, row in df.iterrows():
            xml += f"""
            <TALLYMESSAGE xmlns:UDF="TallyUDF">
                <VOUCHER VCHTYPE="Payment" ACTION="Create">
                    <DATE>{str(row['date']).replace("-", "")[:8]}</DATE>
                    <NARRATION>Auto-Accountant: {row['particulars']}</NARRATION>
                    <ALLLEDGERENTRIES.LIST>
                        <LEDGERNAME>{row['dr_ledger']}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>YES</ISDEEMEDPOSITIVE>
                        <AMOUNT>-{row['base_amt']}</AMOUNT>
                    </ALLLEDGERENTRIES.LIST>
                    <ALLLEDGERENTRIES.LIST><LEDGERNAME>Input CGST</LEDGERNAME><ISDEEMEDPOSITIVE>YES</ISDEEMEDPOSITIVE><AMOUNT>-{row['cgst']}</AMOUNT></ALLLEDGERENTRIES.LIST>
                    <ALLLEDGERENTRIES.LIST><LEDGERNAME>Input SGST</LEDGERNAME><ISDEEMEDPOSITIVE>YES</ISDEEMEDPOSITIVE><AMOUNT>-{row['sgst']}</AMOUNT></ALLLEDGERENTRIES.LIST>
                    <ALLLEDGERENTRIES.LIST>
                        <LEDGERNAME>{row['cr_ledger']}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>NO</ISDEEMEDPOSITIVE>
                        <AMOUNT>{row['total']}</AMOUNT>
                    </ALLLEDGERENTRIES.LIST>
                </VOUCHER>
            </TALLYMESSAGE>"""
        xml += '\n</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
        return xml

# --- UI APP ---
system = UltimateAccountingSystem()
st.set_page_config(page_title="AI Accountant", layout="wide")
st.title("🧙‍♂️ The Auto-Accountant Wizard")

t1, t2, t3 = st.tabs(["📸 Scan Receipt", "🏦 Bulk Bank Import", "📖 Review & Tally Export"])

with t1:
    f = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
    if f:
        img = Image.open(f)
        st.image(img, width=250)
        text = pytesseract.image_to_string(img)
        # Extract amount
        amts = re.findall(r'\d+\.\d{2}', text)
        found_total = float(max(amts, key=float)) if amts else 0.0
        # Auto-map ledger
        suggested_dr = system.auto_map_ledger(text)
        
        with st.form("ocr_form"):
            date = st.date_input("Date", datetime.date.today())
            vend = st.text_input("Vendor", value=text.split('\n')[0][:20])
            total = st.number_input("Total", value=found_total)
            dr = st.selectbox("Category", ["Office Supplies", "Telephone Expense", "Internet Expense", "Conveyance", "Staff Welfare", "Fuel & Oil", "General Expense"], index=6)
            cr = st.selectbox("Paid Via", ["Cash", "HDFC Bank", "ICICI Bank"])
            if st.form_submit_button("Final Post"):
                system.post_entry(str(date), vend, dr, cr, total)
                st.success("Transaction Locked!")

with t2:
    st.info("Upload your Bank Statement CSV here for bulk processing.")
    csv = st.file_uploader("Bank CSV", type="csv")
    if csv:
        b_df = pd.read_csv(csv)
        st.dataframe(b_df.head(5))
        d_col = st.selectbox("Date Col", b_df.columns)
        p_col = st.selectbox("Particulars Col", b_df.columns)
        a_col = st.selectbox("Amount Col", b_df.columns)
        if st.button("🚀 Process Bulk Statement"):
            for _, r in b_df.iterrows():
                # Automatic mapping happens here per row!
                cat = system.auto_map_ledger(str(r[p_col]))
                system.post_entry(str(r[d_col]), str(r[p_col]), cat, "Bank A/c", abs(float(r[a_col])))
            st.balloons()
            st.success("Imported all transactions with Auto-Mapping!")

with t3:
    df = pd.read_sql_query("SELECT * FROM transactions WHERE is_deleted=0", system.conn)
    st.data_editor(df, num_rows="dynamic")
    if not df.empty and st.button("📦 Export All to Tally"):
        xml = system.generate_xml(df)
        st.download_button("Download XML", data=xml, file_name="TallyImport.xml")
