import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import pytesseract
from lxml import etree
import datetime

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect("accounts.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        debit TEXT,
        credit TEXT,
        amount REAL,
        narration TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= OCR =================

def extract_amount(image):
    text = pytesseract.image_to_string(image)
    amount = 0
    for word in text.split():
        word = word.replace(",", "").replace("₹","")
        if word.replace(".", "").isdigit():
            try:
                amount = float(word)
            except:
                pass
    return amount

# ================= DATABASE FUNCTIONS =================

def add_entry(date, debit, credit, amount, narration):
    conn = sqlite3.connect("accounts.db")
    c = conn.cursor()
    c.execute("INSERT INTO journal VALUES(NULL,?,?,?,?,?)",
              (date, debit, credit, amount, narration))
    conn.commit()
    conn.close()

def get_journal():
    conn = sqlite3.connect("accounts.db")
    df = pd.read_sql_query("SELECT * FROM journal", conn)
    conn.close()
    return df

def delete_entry(id):
    conn = sqlite3.connect("accounts.db")
    c = conn.cursor()
    c.execute("DELETE FROM journal WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ================= REPORTS =================

def trial_balance():
    df = get_journal()
    if df.empty:
        return pd.DataFrame()
    debit = df.groupby("debit")["amount"].sum()
    credit = df.groupby("credit")["amount"].sum()
    tb = pd.concat([debit, credit], axis=1)
    tb.columns = ["Debit", "Credit"]
    return tb.fillna(0)

# ================= TALLY EXPORT =================

def export_tally():
    conn = sqlite3.connect("accounts.db")
    c = conn.cursor()
    entries = c.execute("SELECT * FROM journal").fetchall()
    conn.close()

    root = etree.Element("ENVELOPE")
    for e in entries:
        _, date, dr, cr, amt, narr = e
        voucher = etree.SubElement(root, "VOUCHER")
        etree.SubElement(voucher, "DATE").text = date
        etree.SubElement(voucher, "DEBIT").text = dr
        etree.SubElement(voucher, "CREDIT").text = cr
        etree.SubElement(voucher, "AMOUNT").text = str(amt)
        etree.SubElement(voucher, "NARRATION").text = narr

    tree = etree.ElementTree(root)
    tree.write("tally.xml")

# ================= STREAMLIT UI =================

st.set_page_config(page_title="AI Tally Clone", layout="wide")
st.title("🔥 AI Smart Tally Clone App")

# ===== Upload Bill =====
st.header("📸 Upload Bill (Auto Entry)")

uploaded = st.file_uploader("Upload Bill Image", type=["png","jpg","jpeg"])

auto_amount = 0
if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded Bill", width=300)
    auto_amount = extract_amount(img)
    st.success(f"Detected Amount: ₹{auto_amount}")

# ===== Manual Entry Form =====
st.header("🧾 Add Journal Entry")

date = st.date_input("Date", datetime.date.today())
debit = st.text_input("Debit Account", "Purchase")
credit = st.text_input("Credit Account", "Cash")
amount = st.number_input("Amount", value=float(auto_amount))
narration = st.text_input("Narration", "Auto Bill Entry")

if st.button("✅ Add Entry"):
    add_entry(str(date), debit, credit, amount, narration)
    st.success("Entry Added!")

# ===== Journal =====
st.header("📒 Journal Entries")

df = get_journal()
st.dataframe(df)

# Delete Entry
if not df.empty:
    delete_id = st.number_input("Delete Entry ID", step=1)
    if st.button("❌ Delete Entry"):
        delete_entry(delete_id)
        st.success("Deleted!")

# ===== Trial Balance =====
st.header("📊 Trial Balance")
tb = trial_balance()
st.dataframe(tb)

# ===== Export to Tally =====
st.header("🚀 Export to Tally")

if st.button("Generate Tally XML"):
    export_tally()
    st.success("tally.xml Generated! Import in Tally → Gateway → Import Data → Vouchers")
