import streamlit as st
import pandas as pd

# Wczytaj plik Excela (tylko Ty go masz, klient nie widzi)
EXCEL_FILE = r"E:\ACL Operation\1. Deliveries\5. Project Cordination\5. Data Analytics\Power Bi Projects\1. PB2401 Client Information\Client Information - Copy.xlsx"
SHEET_NAME = "CRM_main"

@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
    # oczyszczanie nazw kolumn
    df.columns = df.columns.str.strip()
    return df

st.title("🔎 Status zamówienia")

order_id = st.text_input("Wpisz numer zamówienia (SO / Client PO):")

if order_id:
    df = load_data()
    # filtrujemy po Project SO lub Client PO
    results = df[
        (df["Project SO"].astype(str) == order_id) |
        (df["Client PO"].astype(str) == order_id)
    ]
    if not results.empty:
        st.success("✅ Zamówienie znalezione")
        st.dataframe(results)  # pokazuje tylko dane tego zamówienia
    else:
        st.warning("❌ Nie znaleziono zamówienia")