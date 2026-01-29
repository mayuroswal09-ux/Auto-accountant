import streamlit as st

# This line names your app and adds an icon
st.set_page_config(page_title="My Tally ERP", page_icon="📊", layout="centered")

# ... rest of your code follows below ...
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONNECT TO YOUR PRIVATE CLOUD ---
# This pulls the keys you just saved in the Streamlit Secrets box
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🛡️ My Private Tally ERP")

# --- 2. DATA ENTRY SECTION ---
with st.form("voucher_entry"):
    v_date = st.date_input("Date")
    dr = st.text_input("Debit Ledger")
    cr = st.text_input("Credit Ledger")
    amt = st.number_input("Amount", min_value=0.0)
    
    if st.form_submit_button("Save to My Database"):
        data = {"date": str(v_date), "debit": dr, "credit": cr, "amount": amt}
        supabase.table("vouchers").insert(data).execute()
        st.success("Saved to YOUR Cloud!")

# --- 3. VIEW DATA ---
if st.button("Show My Cloud Records"):
    response = supabase.table("vouchers").select("*").execute()
    df = pd.DataFrame(response.data)
    st.write(df)

