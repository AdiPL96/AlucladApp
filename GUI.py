import streamlit as st
import pandas as pd
from datetime import datetime
import os

STATUS_FLOW = [
    "Add to Production",
    "In Production",
    "In PPC",
    "Transit",
    "Delivered"
]

EXCEL_FILE = r"Client Information.xlsx"
SHEET_NAME = "CRM_main"

# --- INIT FILE ---
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["order_id", "status", "timestamp"])
    df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False)

def load_data():
    return pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

def save_status(order_id, status):
    df = load_data()

    new_row = {
        "order_id": order_id,
        "status": status,
        "timestamp": datetime.now()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False)

def get_order_history(order_id):
    df = load_data()
    return df[df["order_id"] == order_id]

def get_current_status(order_id):
    history = get_order_history(order_id)
    if history.empty:
        return None
    return history.iloc[-1]["status"]

# --- UI ---
st.title("📦 Order Status Tracker")

order_id = st.text_input("Order ID")

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

        for i, status in enumerate(STATUS_FLOW):
            if i < current_index:
                st.markdown(f"✅ **{status}**")
            elif i == current_index:
                st.markdown(f"🔵 **{status}** _(current)_")
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




