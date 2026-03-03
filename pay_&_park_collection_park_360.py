import streamlit as st
import pandas as pd
import plotly.express as px

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

if uploaded_file is None:
    st.info("Please upload an Excel file to continue.")
    st.stop()

# Read File
df = pd.read_excel(uploaded_file)

# Clean column names
df.columns = df.columns.str.strip()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

# Vehicle Type Filter
if "Vehicle Type" in df.columns:
    vehicle_options = df["Vehicle Type"].dropna().unique()
    selected_vehicle = st.sidebar.multiselect(
        "Select Vehicle Type",
        options=vehicle_options,
        default=vehicle_options
    )
    df = df[df["Vehicle Type"].isin(selected_vehicle)]

# Payment Status Filter
if "Payment Status" in df.columns:
    payment_options = df["Paymentstatus Out"].dropna().unique()
    selected_payment = st.sidebar.multiselect(
        "Select Payment Status",
        options=payment_options,
        default=payment_options
    )
    df = df[df["Paymentstatus Out"].isin(selected_payment)]

# Date Filter
if "Entry Time" in df.columns:
    df["Entry Time"] = pd.to_datetime(df["Intime"], errors="coerce")
    min_date = df["Entry Time"].min()
    max_date = df["Entry Time"].max()

    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date]
    )

    if len(date_range) == 2:
        df = df[
            (df["Entry Time"].dt.date >= date_range[0]) &
            (df["Entry Time"].dt.date <= date_range[1])
        ]

# -----------------------------
# KPI Section
# -----------------------------
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_revenue = df["Amount"].sum() if "Amount" in df.columns else 0
total_initial = df["Initial Amount"].sum() if "Initial Amount" in df.columns else 0
total_extra = df["Extra Amount"].sum() if "Extra Amount" in df.columns else 0
total_transactions = len(df)

col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
col2.metric("Total Initial Amount", f"₹{total_initial:,.2f}")
col3.metric("Total Extra Amount", f"₹{total_extra:,.2f}")
col4.metric("Total Transactions", total_transactions)

st.markdown("---")

# -----------------------------
# Revenue by Vehicle Type
# -----------------------------
if "Vehicle Type" in df.columns and "Total Amount" in df.columns:
    st.subheader("Revenue by Vehicle Type")
    rev_vehicle = df.groupby("Vehicle Type")["Amount"].sum().reset_index()
    fig1 = px.bar(rev_vehicle, x="Vehicle Type", y="Total Amount", color="Vehicle Type")
    st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# Payment Status Distribution
# -----------------------------
if "Payment Status" in df.columns:
    st.subheader("Payment Status Distribution")
    pay_status = df["Payment Status"].value_counts().reset_index()
    pay_status.columns = ["Payment Status", "Count"]
    fig2 = px.pie(pay_status, names="Payment Status", values="Count")
    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Hourly Entry Analysis
# -----------------------------
if "Entry Time" in df.columns:
    df["Entry Hour"] = df["Entry Time"].dt.hour
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
# Stay Duration Analysis
# -----------------------------
if "Stay Duration" in df.columns:
    st.subheader("Stay Duration Distribution")
    fig4 = px.histogram(df, x="Stay Duration", nbins=30)
    st.plotly_chart(fig4, use_container_width=True)

# -----------------------------
# Daily Transactions
# -----------------------------
if "Entry Time" in df.columns:
    df["Date"] = df["Entry Time"].dt.date
    daily_transactions = df.groupby("Date").size().reset_index(name="Transactions")

    st.subheader("Daily Transactions")
    fig5 = px.line(daily_transactions, x="Date", y="Transactions")
    st.plotly_chart(fig5, use_container_width=True)
