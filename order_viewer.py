import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------------
# Google Sheets Auth (via st.secrets)
# -----------------------------
def get_gsheet_client():
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

gc = get_gsheet_client()
sheet = gc.open("STEM Explorer Orders").sheet1

# -----------------------------
# Load Data from Google Sheet
# -----------------------------
@st.cache_data(ttl=300)
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = df.columns.str.strip()
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        if "Order Status" not in df.columns:
            df["Order Status"] = "Not Processed"
    return df

df = load_data()
order_statuses = ["Not Processed", "Preparing Order", "Send for Shipping", "Shipped"]

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="📚 STEM Orders", layout="wide")
st.title("📚 STEM Explorer Order Dashboard")

# -----------------------------
# Filters
# -----------------------------
st.subheader("📋 Filter & Update Orders")
col1, col2, col3, col4 = st.columns(4)
with col1:
    name_filter = st.text_input("🔍 Name / Email")
with col2:
    date_range = st.date_input("📅 Date Range", [])
with col3:
    option_filter = st.selectbox("📦 Order Option", ["All", "Book Only", "Book + Arduino Kit"])
with col4:
    status_filter = st.selectbox("🚚 Order Status", ["All"] + order_statuses)

# -----------------------------
# Apply Filters
# -----------------------------
filtered_df = df.copy()

if name_filter:
    filtered_df = filtered_df[
        filtered_df["Name"].str.contains(name_filter, case=False) |
        filtered_df["Email"].str.contains(name_filter, case=False)
    ]

if len(date_range) == 2:
    start, end = date_range
    filtered_df = filtered_df[
        (filtered_df["Timestamp"].dt.date >= start) &
        (filtered_df["Timestamp"].dt.date <= end)
    ]

if option_filter != "All":
    filtered_df = filtered_df[filtered_df["Option"] == option_filter]

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["Order Status"] == status_filter]

# -----------------------------
# Order Table with Status Dropdowns
# -----------------------------
st.markdown(f"### Showing {len(filtered_df)} record(s)")

for i, row in filtered_df.iterrows():
    col_data = st.columns([2, 2, 2, 2, 2, 2, 2])
    col_data[0].markdown(f"**{row['Timestamp'].strftime('%Y-%m-%d %H:%M')}**")
    col_data[1].write(row["Name"])
    col_data[2].write(row["Email"])
    col_data[3].write(row["Option"])
    col_data[4].write(f"RM {row['Total Cost']}")
    col_data[5].markdown(f"[📎 Receipt]({row['Receipt Link']})")

    current_status = row["Order Status"]
    new_status = col_data[6].selectbox(
        "Status",
        order_statuses,
        index=order_statuses.index(current_status),
        key=f"status_{i}"
    )

    if new_status != current_status:
        if st.button("✅ Save", key=f"save_{i}"):
            sheet.update_cell(i + 2, df.columns.get_loc("Order Status") + 1, new_status)
            st.success(f"Status updated for {row['Name']} to {new_status}")
            st.experimental_rerun()

# -----------------------------
# Summary + CSV Download
# -----------------------------
with st.expander("📈 Summary Report"):
    st.write(f"🧾 Total Orders: {len(df)}")
    st.write(f"📦 Book Only: {len(df[df['Option'] == 'Book Only'])}")
    st.write(f"🔧 Book + Arduino Kit: {len(df[df['Option'] == 'Book + Arduino Kit'])}")
    st.write(f"💰 Total Sales (RM): {df['Total Cost'].sum():,.2f}")

csv = filtered_df.to_csv(index=False)
st.download_button("⬇️ Download CSV", csv, "stem_orders_report.csv", "text/csv")
