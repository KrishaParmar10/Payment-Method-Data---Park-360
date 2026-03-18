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
    st.subheader("Revenue by Vehicle Type")
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
    st.subheader("Payment Status Distribution")
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
    st.subheader("Hourly Entries")
    fig3 = px.bar(
        x=entry_hourly.index,
        y=entry_hourly.values,
        labels={"x": "Hour", "y": "Entries"}
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Hourly Exits")
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


# Convert Date & Time

df["Entry Time"] = pd.to_datetime(df["Intime"])
df["Exit Time"] = pd.to_datetime(df["Outtime"])

df["Date"] = df["Entry Time"].dt.date
df["Hour"] = df["Entry Time"].dt.hour
df["Day"] = df["Entry Time"].dt.day_name()



# INTIME / OUTTIME ANALYSIS

st.header("Intime / Outtime Analysis")

col1, col2 = st.columns(2)

entry_hour = df.groupby("Hour").size().reset_index(name="Entries")

with col1:
    fig = px.bar(entry_hour, x="Hour", y="Entries", title="Entries per Hour")
    st.plotly_chart(fig, use_container_width=True)

peak_hour = entry_hour.loc[entry_hour["Entries"].idxmax(), "Hour"]
st.success(f"Peak Entry Hour: {peak_hour}:00")

# Weekday vs Weekend
df["Type"] = df["Day"].apply(lambda x: "Weekend" if x in ["Saturday", "Sunday"] else "Weekday")

weekday_data = df.groupby(["Hour", "Type"]).size().reset_index(name="Count")

fig = px.line(weekday_data, x="Hour", y="Count", color="Type",
              title="Weekday vs Weekend Traffic")
st.plotly_chart(fig, use_container_width=True)


# 7-DAY TREND ANALYSIS

st.header("7-Day Trend Analysis")

daily = df.groupby("Date")["Amount"].sum().reset_index()
daily["Average"] = daily["Amount"].mean()
daily["Variance"] = daily["Amount"] - daily["Average"]

fig = px.line(daily, x="Date", y="Total Amount", title="Daily Revenue Trend")
st.plotly_chart(fig, use_container_width=True)

st.write("### Variance from Average")
st.dataframe(daily)


# OPERATOR PERFORMANCE

if "Operator" in df.columns:

    st.header("Operator Performance")

    operator_perf = df.groupby("Operator")["Total Amount"].sum().reset_index()
    operator_perf = operator_perf.sort_values(by="Total Amount", ascending=False)

    fig = px.bar(operator_perf, x="Operator", y="Total Amount",
                 title="Operator Revenue Ranking")
    st.plotly_chart(fig, use_container_width=True)

    # Payment split
    if "Payment Mode" in df.columns:
        pay_split = df.groupby(["Operator", "Payment Mode"]).size().reset_index(name="Count")

        fig = px.bar(pay_split, x="Operator", y="Count", color="Payment Mode",
                     title="Operator Payment Mode Distribution")
        st.plotly_chart(fig, use_container_width=True)


# PAYMENT MODE INSIGHTS

if "Payment Mode" in df.columns:

    st.header("Payment Mode Insights")

    pay_trend = df.groupby(["Date", "Payment Mode"]).size().reset_index(name="Count")

    fig = px.line(pay_trend, x="Date", y="Count", color="Payment Mode",
                  title="Payment Mode Trend")
    st.plotly_chart(fig, use_container_width=True)

    # Digital Adoption
    digital = df[df["Payment Mode"].isin(["UPI", "Card"])]
    digital_percent = (len(digital) / len(df)) * 100

    st.metric("Digital Adoption %", f"{digital_percent:.2f}%")
