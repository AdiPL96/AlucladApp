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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "Client Information App.xlsx")
SHEET_NAME = "CRM main"

# --- UTILS ---
def normalize_order_id(order_id):
    return str(order_id).strip().upper()


# --- INIT FILE ---
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=[
        "order_id",
        "status",
        "timestamp",
        "project",
        "materials",
        "delivery address",
        "estimated delivery date"
    ])
    df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False)


def load_data():
    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name=SHEET_NAME,
        dtype=str,
        engine="openpyxl"
    )

    df.columns = df.columns.str.strip().str.lower()

    ORDER_ID_ALIASES = {
        "order_id",
        "order id",
        "orderid",
        "id",
        "order number",
        "order_number",
    }

    matched_column = None
    for col in df.columns:
        if col.replace("_", " ") in ORDER_ID_ALIASES:
            matched_column = col
            break

    if not matched_column:
        raise ValueError(
            f"Brak kolumny order_id. Dostępne kolumny: {df.columns.tolist()}"
        )

    if matched_column != "order_id":
        df = df.rename(columns={matched_column: "order_id"})

    df["order_id"] = df["order_id"].apply(normalize_order_id)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        df["timestamp"] = pd.NaT

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


def get_order_info(order_id):
    """
    Zwraca podstawowe informacje o zamówieniu:
    Project, Materials, Delivery Address, Estimated Delivery Date.
    """
    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name=SHEET_NAME,
        dtype=str,
        engine="openpyxl"
    )

    df.columns = df.columns.str.strip().str.lower()

    ORDER_ID_ALIASES = {
        "order_id",
        "order id",
        "orderid",
        "id",
        "order number",
        "order_number",
    }

    matched_column = None
    for col in df.columns:
        if col.replace("_", " ") in ORDER_ID_ALIASES:
            matched_column = col
            break

    if not matched_column:
        raise ValueError(f"Brak kolumny order_id w Excelu: {df.columns.tolist()}")

    if matched_column != "order_id":
        df = df.rename(columns={matched_column: "order_id"})

    df["order_id"] = df["order_id"].apply(normalize_order_id)

    row = df[df["order_id"] == order_id]

    if not row.empty:
        return {
            "Project": row.iloc[0].get("project", ""),
            "Materials": row.iloc[0].get("materials", ""),
            "Delivery Address": row.iloc[0].get("delivery address", ""),
            "Estimated Delivery Date": row.iloc[0].get("estimated delivery date", "")
        }

    return None


def get_order_history(order_id):
    df = load_data()
    order_id = normalize_order_id(order_id)
    return df[df["order_id"] == order_id]


def get_current_status(order_id):
    history = get_order_history(order_id)

    if history.empty:
        return None

    history = history.sort_values("timestamp")
    return history.iloc[-1]["status"]


# --- UI ---
st.title("📦 Order Status Tracker")

raw_order_id = st.text_input("Order ID")
order_id = normalize_order_id(raw_order_id)

if st.button("Create Order"):
    if order_id:
        save_status(order_id, STATUS_FLOW[0])
        st.success("Order created")

status_times = {}

if order_id:
    history = get_order_history(order_id)
    order_info = get_order_info(order_id)

    if order_info is not None:
        project = order_info.get("Project", "")
        materials = order_info.get("Materials", "")
        delivery_address = order_info.get("Delivery Address", "")
        estimated_delivery_date = order_info.get("Estimated Delivery Date", "")

        st.markdown(
            f"**Project:** {project} | "
            f"**Materials:** {materials} | "
            f"**Delivery Address:** {delivery_address}"
        )

        if not history.empty:
            history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
            history = history.sort_values("timestamp")

            current_status = history.iloc[-1]["status"]

            if current_status in STATUS_FLOW:
                current_index = STATUS_FLOW.index(current_status)

                st.subheader("Status timeline")

                status_times = {}
                for status in STATUS_FLOW:
                    ts_rows = history[history["status"] == status]
                    status_times[status] = (
                        ts_rows.iloc[-1]["timestamp"] if not ts_rows.empty else None
                    )

                for i, status in enumerate(STATUS_FLOW):
                    ts = status_times[status]
                    ts_str = ts.strftime("%Y-%m-%d %H:%M") if pd.notna(ts) else ""

                    if i < current_index:
                        st.markdown(f"✅ **{status}** - _{ts_str}_")
                    elif i == current_index:
                        st.markdown(f"🔵 **{status}** _(current)_ - _{ts_str}_")
                    else:
                        st.markdown(f"⚪ {status} - _{ts_str}_")

                if estimated_delivery_date:
                    st.info(f"📅 Estimated Delivery Date: {estimated_delivery_date}")
                else:
                    st.info("📅 Estimated Delivery Date: not available")

                next_status = (
                    STATUS_FLOW[current_index + 1]
                    if current_index + 1 < len(STATUS_FLOW)
                    else None
                )

                if next_status:
                    if st.button(
                        f"➡️ Move to '{next_status}'",
                        key=f"move_btn_{order_id}_{next_status}"
                    ):
                        save_status(order_id, next_status)
                        st.rerun()
                else:
                    st.success("Order delivered ✅")

            else:
                st.warning(f"Unknown status in Excel: {current_status}")

        else:
            st.info("No status history for this order yet")

            if estimated_delivery_date:
                st.info(f"📅 Estimated Delivery Date: {estimated_delivery_date}")
            else:
                st.info("📅 Estimated Delivery Date: not available")

    else:
        st.info("Order not found")






























