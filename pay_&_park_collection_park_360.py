import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Parking Analytics Dashboard", layout="wide")

st.title("🚗 Parking Management Analytics Dashboard")

# File Upload
uploaded_file = st.file_uploader(""C:\Users\KRISHA\Desktop\PARK 360\Paymet data\Pay_Park_Collection_Report.xlsx"", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel("C:\Users\KRISHA\Desktop\PARK 360\Paymet data\Pay_Park_Collection_Report.xlsx")
else:
    st.info(""C:\Users\KRISHA\Desktop\PARK 360\Paymet data\Pay_Park_Collection_Report.xlsx"")
    df = pd.read_excel(""C:\Users\KRISHA\Desktop\PARK 360\Paymet data\Pay_Park_Collection_Report.xlsx"")

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

if "Vehicle Type" in df.columns:
    vehicle_types = st.sidebar.multiselect(
        "Select Vehicle Type",
        options=df["Vehicle Type"].unique(),
        default=df["Vehicle Type"].unique()
    )
    df = df[df["Vehicle Type"].isin(vehicle_types)]

# -----------------------------
# KPI Section
# -----------------------------
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_revenue = df["Total Amount"].sum()
total_initial = df["Initial Amount"].sum()
total_extra = df["Extra Amount"].sum()
total_transactions = len(df)

col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
col2.metric("Total Initial Amount", f"₹{total_initial:,.2f}")
col3.metric("Total Extra Amount", f"₹{total_extra:,.2f}")
col4.metric("Total Transactions", total_transactions)

# -----------------------------
# Revenue by Vehicle Type
# -----------------------------
if "Vehicle Type" in df.columns:
    st.subheader("💰 Revenue by Vehicle Type")
    rev_vehicle = df.groupby("Vehicle Type")["Total Amount"].sum().reset_index()
    fig1 = px.bar(rev_vehicle, x="Vehicle Type", y="Total Amount", color="Vehicle Type")
    st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# Payment Status Counts
# -----------------------------
if "Payment Status" in df.columns:
    st.subheader("💳 Payment Status Distribution")
    pay_status = df["Payment Status"].value_counts().reset_index()
    pay_status.columns = ["Payment Status", "Count"]
    fig2 = px.pie(pay_status, names="Payment Status", values="Count")
    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Entry and Exit Analysis
# -----------------------------
if "Entry Time" in df.columns and "Exit Time" in df.columns:

    df["Entry Time"] = pd.to_datetime(df["Entry Time"])
    df["Exit Time"] = pd.to_datetime(df["Exit Time"])

    df["Entry Hour"] = df["Entry Time"].dt.hour
    df["Exit Hour"] = df["Exit Time"].dt.hour

    entry_hourly = df["Entry Hour"].value_counts().sort_index()
    exit_hourly = df["Exit Hour"].value_counts().sort_index()

    st.subheader("⏰ Hourly Entry & Exit Count")

    col1, col2 = st.columns(2)

    with col1:
        fig3 = px.bar(
            x=entry_hourly.index,
            y=entry_hourly.values,
            labels={"x": "Hour", "y": "Entries"},
            title="Entries Per Hour"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = px.bar(
            x=exit_hourly.index,
            y=exit_hourly.values,
            labels={"x": "Hour", "y": "Exits"},
            title="Exits Per Hour"
        )
        st.plotly_chart(fig4, use_container_width=True)

    peak_entry_hour = entry_hourly.idxmax()
    peak_exit_hour = exit_hourly.idxmax()

    st.success(f"Peak Entry Hour: {peak_entry_hour}:00")
    st.success(f"Peak Exit Hour: {peak_exit_hour}:00")

# -----------------------------
# Stay Duration Analysis
# -----------------------------
if "Stay Duration" in df.columns:
    st.subheader("🕒 Stay Duration Distribution")
    fig5 = px.histogram(df, x="Stay Duration", nbins=30)
    st.plotly_chart(fig5, use_container_width=True)

# -----------------------------
# Average Duration by Vehicle Type
# -----------------------------
if "Vehicle Type" in df.columns and "Stay Duration" in df.columns:
    st.subheader("📈 Average Duration by Vehicle Type")
    avg_duration = df.groupby("Vehicle Type")["Stay Duration"].mean().reset_index()
    fig6 = px.bar(avg_duration, x="Vehicle Type", y="Stay Duration", color="Vehicle Type")
    st.plotly_chart(fig6, use_container_width=True)

# -----------------------------
# Daily Transactions
# -----------------------------
if "Entry Time" in df.columns:
    df["Date"] = df["Entry Time"].dt.date
    daily_transactions = df.groupby("Date").size().reset_index(name="Transactions")

    st.subheader("📅 Total Transactions Per Day")
    fig7 = px.line(daily_transactions, x="Date", y="Transactions")
    st.plotly_chart(fig7, use_container_width=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("Dynamic Parking Analytics Dashboard built with Streamlit")
