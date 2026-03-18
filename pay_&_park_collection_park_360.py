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

fig = px.line(daily, x="Date", y="Amount", title="Daily Revenue Trend")
st.plotly_chart(fig, use_container_width=True)

st.write("### Variance from Average")
st.dataframe(daily)


st.header("Operator Performance")

# Clean column names
df.columns = df.columns.str.strip()

# --------- AUTO DETECT COLUMN NAMES ----------
operator_col = None
amount_col = None
payment_col = None
date_col = None

for col in df.columns:
    if "operator" in col.lower():
        operator_col = col
    if "amount" in col.lower():
        amount_col = col
    if "payment" in col.lower() or "mode" in col.lower():
        payment_col = col
    if "entry" in col.lower() or "date" in col.lower():
        date_col = col

# --------- VALIDATION ----------
if operator_col is None or amount_col is None:
    st.error("Operator or Amount column not found in your data")
    st.stop()

# Convert date
df[date_col] = pd.to_datetime(df[date_col])
df["Date"] = df[date_col].dt.date

# --------- CONSISTENCY CALCULATION ----------
# Daily revenue per operator
daily_op = df.groupby([operator_col, "Date"])[amount_col].sum().reset_index()

# Mean + Std deviation (consistency)
consistency = daily_op.groupby(operator_col)[amount_col].agg(["mean", "std"]).reset_index()

# Lower std = more consistent
consistency["Consistency Score"] = consistency["mean"] / (consistency["std"] + 1)

consistency = consistency.sort_values(by="Consistency Score", ascending=False)

st.subheader("Operator Consistency Ranking")
st.dataframe(consistency)

# --------- VISUAL ----------
import plotly.express as px

fig = px.bar(consistency,
             x=operator_col,
             y="Consistency Score",
             title="Operator Consistency Ranking",
             color="Consistency Score")

st.plotly_chart(fig, use_container_width=True)

# --------- PAYMENT BEHAVIOR ----------
if payment_col:

    st.subheader("Payment Behavior by Operator")

    pay = df.groupby([operator_col, payment_col]).size().reset_index(name="Count")

    fig2 = px.bar(pay,
                  x=operator_col,
                  y="Count",
                  color=payment_col,
                  title="Cash vs Digital by Operator")

    st.plotly_chart(fig2, use_container_width=True)

    # --------- DIGITAL vs CASH SUMMARY ----------
    digital_keywords = ["upi", "card", "online"]
    
    df["Payment_Type"] = df[payment_col].astype(str).str.lower().apply(
        lambda x: "Digital" if any(k in x for k in digital_keywords) else "Cash"
    )

    summary = df.groupby([operator_col, "Payment_Type"]).size().reset_index(name="Count")

    pivot = summary.pivot(index=operator_col, columns="Payment_Type", values="Count").fillna(0)

    st.subheader("Digital vs Cash Summary")
    st.dataframe(pivot)

    # Highlight top performers
    if "Digital" in pivot.columns:
        top_digital = pivot["Digital"].idxmax()
        st.success(f"Top Digital Driver: {top_digital}")

    if "Cash" in pivot.columns:
        top_cash = pivot["Cash"].idxmax()
        st.warning(f"Highest Cash Collector: {top_cash}")

else:
    st.warning("Payment Mode column not found")
