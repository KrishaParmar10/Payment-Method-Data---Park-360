import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="Parking Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.image("Park360 Logo.png")

st.title("Parking Management Analytics Dashboard")

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload Parking Report Excel File", type=["xlsx"])

st.sidebar.title("Filters")

if uploaded_file is None:
    st.info("Please upload an Excel file to continue.")
    st.stop()

# -----------------------------
# Read File
# -----------------------------
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()

# Convert datetime
df["Intime"] = pd.to_datetime(df["Intime"], errors="coerce")
df["Outtime"] = pd.to_datetime(df["Outtime"], errors="coerce")

# -----------------------------
# FILTERS
# -----------------------------

# Vehicle Type Filter
vehicle_options = df["Vehicletype"].dropna().unique()
selected_vehicle = st.sidebar.multiselect(
    "Select Vehicle Type",
    options=vehicle_options,
    default=vehicle_options
)
df = df[df["Vehicletype"].isin(selected_vehicle)]

# Payment Status Filter
payment_options = df["Paymentstatus Out"].dropna().unique()
selected_payment = st.sidebar.multiselect(
    "Select Payment Status",
    options=payment_options,
    default=payment_options
)
df = df[df["Paymentstatus Out"].isin(selected_payment)]

# Date Filter
min_date = df["Intime"].min()
max_date = df["Intime"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date]
)

if len(date_range) == 2:
    df = df[
        (df["Intime"].dt.date >= date_range[0]) &
        (df["Intime"].dt.date <= date_range[1])
    ]

# -----------------------------
# KPI SECTION
# -----------------------------
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_revenue = df["Amount"].sum()
total_initial = df["Initial Amount"].sum()
total_extra = df["Extra Amount"].sum()
total_transactions = len(df)

col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
col2.metric("Total Initial Amount", f"₹{total_initial:,.2f}")
col3.metric("Total Extra Amount", f"₹{total_extra:,.2f}")
col4.metric("Total Transactions", total_transactions)

st.markdown("---")

# -----------------------------
# Side by Side Charts
# -----------------------------
col1, col2 = st.columns(2)

# Revenue by Vehicle Type
with col1:
    st.subheader("💰 Revenue by Vehicle Type")
    rev_vehicle = df.groupby("Vehicletype")["Amount"].sum().reset_index()
    fig1 = px.bar(
        rev_vehicle,
        x="Vehicletype",
        y="Amount",
        color="Vehicletype"
    )
    st.plotly_chart(fig1, use_container_width=True)

# Payment Status Distribution
with col2:
    st.subheader("💳 Payment Status Distribution")
    pay_status = df["Paymentstatus Out"].value_counts().reset_index()
    pay_status.columns = ["Paymentstatus Out", "Count"]
    fig2 = px.pie(
        pay_status,
        names="Paymentstatus Out",
        values="Count"
    )
    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Hourly Entry & Exit (Side by Side)
# -----------------------------
col3, col4 = st.columns(2)

df["Entry Hour"] = df["Intime"].dt.hour
df["Exit Hour"] = df["Outtime"].dt.hour

entry_hourly = df["Entry Hour"].value_counts().sort_index()
exit_hourly = df["Exit Hour"].value_counts().sort_index()

with col3:
    st.subheader("⏰ Hourly Entries")
    fig3 = px.bar(
        x=entry_hourly.index,
        y=entry_hourly.values,
        labels={"x": "Hour", "y": "Entries"}
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("🚪 Hourly Exits")
    fig4 = px.bar(
        x=exit_hourly.index,
        y=exit_hourly.values,
        labels={"x": "Hour", "y": "Exits"}
    )
    st.plotly_chart(fig4, use_container_width=True)

# -----------------------------
# Daily Transactions
# -----------------------------
df["Date"] = df["Intime"].dt.date
daily_transactions = df.groupby("Date").size().reset_index(name="Transactions")

st.subheader("Daily Transactions")
fig4 = px.line(daily_transactions, x="Date", y="Transactions")
st.plotly_chart(fig4, use_container_width=True)
