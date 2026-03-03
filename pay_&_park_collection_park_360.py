import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page Config
# -----------------------------

col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.image("Park360_Logo.png", width=250)


st.set_page_config(
    page_title="Parking Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# Revenue by Vehicle Type
# -----------------------------
st.subheader("Revenue by Vehicle Type")
rev_vehicle = df.groupby("Vehicletype")["Amount"].sum().reset_index()
fig1 = px.bar(rev_vehicle, x="Vehicletype", y="Amount", color="Vehicletype")
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# Payment Status Distribution
# -----------------------------
st.subheader("Payment Status Distribution")
pay_status = df["Paymentstatus Out"].value_counts().reset_index()
pay_status.columns = ["Paymentstatus Out", "Count"]
fig2 = px.pie(pay_status, names="Paymentstatus Out", values="Count")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Hourly Entry Analysis
# -----------------------------
df["Entry Hour"] = df["Intime"].dt.hour
entry_hourly = df["Entry Hour"].value_counts().sort_index()

st.subheader("Hourly Entries")
fig3 = px.bar(
    x=entry_hourly.index,
    y=entry_hourly.values,
    labels={"x": "Hour", "y": "Entries"}
)
st.plotly_chart(fig3, use_container_width=True)

if not entry_hourly.empty:
    peak_hour = entry_hourly.idxmax()
    st.success(f"Peak Entry Hour: {peak_hour}:00")

# -----------------------------
# Hourly Exit Analysis
# -----------------------------
df["Exit Hour"] = df["Outtime"].dt.hour
exit_hourly = df["Exit Hour"].value_counts().sort_index()

st.subheader("Hourly Exits")
fig_exit = px.bar(
    x=exit_hourly.index,
    y=exit_hourly.values,
    labels={"x": "Hour", "y": "Exits"}
)
st.plotly_chart(fig_exit, use_container_width=True)

if not exit_hourly.empty:
    peak_exit_hour = exit_hourly.idxmax()
    st.success(f"Peak Exit Hour: {peak_exit_hour}:00")

# -----------------------------
# Daily Transactions
# -----------------------------
df["Date"] = df["Intime"].dt.date
daily_transactions = df.groupby("Date").size().reset_index(name="Transactions")

st.subheader("Daily Transactions")
fig4 = px.line(daily_transactions, x="Date", y="Transactions")
st.plotly_chart(fig4, use_container_width=True)
