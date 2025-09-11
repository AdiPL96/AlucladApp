import streamlit as st
import pandas as pd

# Wczytaj plik Excela (tylko Ty go masz, klient nie widzi)
EXCEL_FILE = "Client Information - Copy.xlsx"
SHEET_NAME = "CRM_main"

@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
    # oczyszczanie nazw kolumn
    df.columns = df.columns.str.strip()
    return df

st.title("🔎 Status of Orders")

order_id = st.text_input("Please text number of your PO (SO / Client PO):")

if order_id:
    df = load_data()
    # filtrujemy po Project SO lub Client PO
    results = df[
        (df["Project SO"].astype(str) == order_id) |
        (df["Client PO"].astype(str) == order_id)
    ]
    if not results.empty:
        st.success("✅ Order found")
        st.dataframe(results)  # pokazuje tylko dane tego zamówienia
    else:

        st.warning("❌ No order found")

