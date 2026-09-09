import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(
    page_title="Order Status Tracker",
    page_icon="📦",
    layout="centered"
)

STATUS_FLOW = [
    "Awaiting",
    "Add to Production",
    "In production",
    "In PPC",
    "Transit",
    "Delivered"
]

SHEET_NAME = "CRM main"

try:
    EXCEL_URL = st.secrets["EXCEL_URL"]
except Exception:
    EXCEL_URL = None


def normalize_order_id(order_id):
    return str(order_id).strip().upper()


def clean_display_value(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    value = str(value).strip()

    if value.lower() in ["nan", "none", "nat"]:
        return ""

    return value


@st.cache_data(ttl=60)
def download_excel():
    if not EXCEL_URL:
        raise RuntimeError("Brak EXCEL_URL w Streamlit Secrets.")

    response = requests.get(
        EXCEL_URL,
        timeout=30,
        allow_redirects=True
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Nie udało się pobrać pliku Excel. HTTP {response.status_code}"
        )

    content_type = response.headers.get("content-type", "").lower()

    if "text/html" in content_type:
        raise RuntimeError(
            "Link zwrócił stronę HTML zamiast pliku Excel. "
            "Potrzebny jest bezpośredni link do pobrania pliku."
        )

    return response.content


@st.cache_data(ttl=60)
def load_data():
    excel_bytes = download_excel()

    df = pd.read_excel(
        BytesIO(excel_bytes),
        sheet_name=SHEET_NAME,
        dtype=str,
        engine="openpyxl"
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    order_id_aliases = {
        "order_id",
        "order id",
        "orderid",
        "id",
        "order number",
        "order_number",
    }

    matched_column = None

    for col in df.columns:
        normalized_col = col.replace("_", " ").strip()

        if normalized_col in order_id_aliases:
            matched_column = col
            break

    if not matched_column:
        raise ValueError(
            "Brak kolumny order_id. "
            f"Dostępne kolumny: {df.columns.tolist()}"
        )

    if matched_column != "order_id":
        df = df.rename(columns={matched_column: "order_id"})

    df["order_id"] = (
        df["order_id"]
        .fillna("")
        .apply(normalize_order_id)
    )

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )
    else:
        df["timestamp"] = pd.NaT

    return df


def get_order_rows(order_id):
    df = load_data()
    order_id = normalize_order_id(order_id)
    return df[df["order_id"] == order_id].copy()


def get_order_info(order_id):
    rows = get_order_rows(order_id)

    if rows.empty:
        return None

    def first_non_empty(column_name):
        if column_name not in rows.columns:
            return ""

        for value in rows[column_name].tolist():
            cleaned = clean_display_value(value)
            if cleaned:
                return cleaned

        return ""

    return {
        "Project": first_non_empty("project"),
        "Materials": first_non_empty("materials"),
        "Delivery Address": first_non_empty("delivery address"),
        "Estimated Delivery Date": first_non_empty("estimated delivery date"),
        "Awaiting Reason": first_non_empty("awaiting reason")
    }


def get_order_history(order_id):
    rows = get_order_rows(order_id)

    if rows.empty:
        return rows

    if "timestamp" in rows.columns:
        rows = rows.sort_values("timestamp", na_position="last")

    return rows


def get_current_status(order_id):
    history = get_order_history(order_id)

    if history.empty:
        return None

    if "status" not in history.columns:
        return None

    valid = history[
        history["status"].notna()
        & (history["status"].astype(str).str.strip() != "")
    ]

    if valid.empty:
        return None

    return clean_display_value(valid.iloc[-1]["status"])


def get_status_times(history):
    result = {}

    for status in STATUS_FLOW:
        if "status" not in history.columns:
            result[status] = None
            continue

        status_rows = history[
            history["status"].astype(str).str.strip() == status
        ]

        if status_rows.empty:
            result[status] = None
            continue

        result[status] = status_rows.iloc[-1].get("timestamp", pd.NaT)

    return result


st.title("📦 Order Status Tracker")
st.caption("Enter your Order ID to view the latest project status.")

raw_order_id = st.text_input(
    "Order ID",
    placeholder="e.g. 12858"
)

order_id = normalize_order_id(raw_order_id)

if not EXCEL_URL:
    st.error("Configuration error: EXCEL_URL is not set.")
    st.info("Add EXCEL_URL to Streamlit Cloud -> Settings -> Secrets.")
    st.stop()

if order_id:
    try:
        history = get_order_history(order_id)
        order_info = get_order_info(order_id)

    except Exception as exc:
        st.error("The order database could not be loaded.")

        with st.expander("Technical details"):
            st.code(str(exc))

        st.stop()

    if order_info is None or history.empty:
        st.warning("Order not found.")

    else:
        project = clean_display_value(order_info.get("Project"))
        materials = clean_display_value(order_info.get("Materials"))
        delivery_address = clean_display_value(order_info.get("Delivery Address"))
        estimated_delivery_date = clean_display_value(
            order_info.get("Estimated Delivery Date")
        awaiting_reason = clean_display_value(
            order_info.get("Awaiting Reason")
        )

        st.markdown("---")
        st.subheader(f"Order {order_id}")

        info_lines = []

        if project:
            info_lines.append(f"**Project:** {project}")

        if materials:
            info_lines.append(f"**Materials:** {materials}")

        if delivery_address:
            info_lines.append(f"**Delivery Address:** {delivery_address}")

        if info_lines:
            st.markdown("  \n".join(info_lines))

        current_status = get_current_status(order_id)
        
        if current_status == "Awaiting" and awaiting_reason:
            st.warning(f"⏳ Awaiting: {awaiting_reason}")

        if not current_status:
            st.info("No status information is available for this order yet.")

        elif current_status not in STATUS_FLOW:
            st.warning(f"Unknown status in source data: {current_status}")

        else:
            current_index = STATUS_FLOW.index(current_status)

            st.subheader("Status timeline")

            status_times = get_status_times(history)

            for i, status in enumerate(STATUS_FLOW):
                ts = status_times.get(status)
                ts_str = ""

                if pd.notna(ts):
                    ts_str = ts.strftime("%Y-%m-%d %H:%M")

                if i < current_index:
                    st.markdown(
                        f"✅ **{status}**"
                        + (f" — _{ts_str}_" if ts_str else "")
                    )

                elif i == current_index:
                    st.markdown(
                        f"🔵 **{status}** _(current)_"
                        + (f" — _{ts_str}_" if ts_str else "")
                    )

                else:
                    st.markdown(f"⚪ {status}")

        if estimated_delivery_date:
            st.info(
                "📅 Estimated Delivery Date: "
                f"{estimated_delivery_date}"
            )
        else:
            st.info("📅 Estimated Delivery Date: TBC")

        if (
            "timestamp" in history.columns
            and history["timestamp"].notna().any()
        ):
            last_updated = history["timestamp"].dropna().max()

            st.caption(
                "Last updated: "
                + last_updated.strftime("%Y-%m-%d %H:%M")
            )

st.markdown("---")

st.caption(
    "Order information is provided for tracking purposes "
    "and may be subject to operational updates."
)
