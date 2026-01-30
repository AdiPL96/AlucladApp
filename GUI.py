import streamlit as st
import pandas as pd
from datetime import datetime
import os

STATUS_FLOW = [
    "Add to Production",
    "In production",
    "In PPC",
    "Transit",
    "Delivered"
]

EXCEL_FILE = r"Client Information App.xlsx"
SHEET_NAME = "CRM_main"

# --- UTILS ---
def normalize_order_id(order_id):
    return str(order_id).strip().upper()

# --- INIT FILE ---
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["order_id", "status", "timestamp"])
    df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False)

def load_data():
    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name=SHEET_NAME,
        dtype=str
    )

    # normalizacja nazw kolumn
    df.columns = df.columns.str.strip().str.lower()

    # możliwe warianty kolumny order_id
    ORDER_ID_ALIASES = {
        "order_id",
        "order id",
        "orderid",
        "id",
        "order number",
        "order_number",
    }

    # znajdź kolumnę z order_id
    matched_column = None
    for col in df.columns:
        if col.replace("_", " ") in ORDER_ID_ALIASES:
            matched_column = col
            break

    if not matched_column:
        raise ValueError(
            f"Brak kolumny order_id. Dostępne kolumny: {df.columns.tolist()}"
        )

    # ujednolicenie nazwy
    if matched_column != "order_id":
        df = df.rename(columns={matched_column: "order_id"})

    # normalizacja danych
    df["order_id"] = df["order_id"].apply(normalize_order_id)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df

def save_status(order_id, status):
    df = load_data()

    order_id = normalize_order_id(order_id)

    new_row = {
        "order_id": order_id,
        "status": status,
        "timestamp": datetime.now()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False)

def get_order_history(order_id):
    df = load_data()
    order_id = normalize_order_id(order_id)
    return df[df["order_id"] == order_id]

def get_current_status(order_id):
    history = get_order_history(order_id)
    if history.empty:
        return None
    return history.iloc[-1]["status"]

# --- UI ---
st.title("📦 Order Status Tracker")

raw_order_id = st.text_input("Order ID")
order_id = normalize_order_id(raw_order_id)

if st.button("Create Order"):
    if order_id:
        save_status(order_id, STATUS_FLOW[0])
        st.success("Order created")

if order_id:
    history = get_order_history(order_id)

    if not history.empty:
        current_status = history.iloc[-1]["status"]
        current_index = STATUS_FLOW.index(current_status)

        st.subheader("Status timeline")

# bierzemy ostatni timestamp dla każdego statusu
status_times = (
    .history()
    .groupby("status")["timestamp"]
    .last()
    .to_dict()
)

for i, status in enumerate(STATUS_FLOW):
    ts = status_times.get(status)

    ts_str = (
        ts.strftime("%d/%m/%Y %H:%M")
        if pd.notna(ts)
        else ""
    )

    if i < current_index:
        st.markdown(f"✅ *{status}* {ts_str}")
    elif i == current_index:
        st.markdown(f"🔵 *{status}* {ts_str} (current)")
    else:
        st.markdown(f"⚪ {status}")

        next_status = (
            STATUS_FLOW[current_index + 1]
            if current_index + 1 < len(STATUS_FLOW)
            else None
        )

        if next_status:
            if st.button(f"➡️ Move to '{next_status}'"):
                save_status(order_id, next_status)
                st.experimental_rerun()
        else:
            st.info("Order not found")












