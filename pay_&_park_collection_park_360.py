import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG & SIMPLIFIED STYLING
# ─────────────────────────────────────────────
st.set_page_config(page_title="Park 360 Manager", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f9f9f9; }
    h1, h2, h3 { color: #1e3d59; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA PROCESSING (CLEANED)
# ─────────────────────────────────────────────
def load_and_clean(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    
    # Convert Times
    df["Intime"] = pd.to_datetime(df["Intime"], errors="coerce")
    df["Outtime"] = pd.to_datetime(df["Outtime"], errors="coerce")
    
    # Clean Currency Columns
    for col in ["Initial Amount", "Extra Amount", "Amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[₹,\s]", "", regex=True), errors="coerce").fillna(0)
    
    # Simple Time Features
    df["Date"] = df["Intime"].dt.date
    df["Hour"] = df["Intime"].dt.hour
    df["DayType"] = df["Intime"].dt.dayofweek.apply(lambda x: "Weekend" if x >= 5 else "Weekday")
    
    # Payment Category
    digital_keys = ["UPI", "CARD", "FASTAG", "ONLINE"]
    pay_col = "Extra Paymenttype C" if "Extra Paymenttype C" in df.columns else None
    if pay_col:
        df["Mode"] = df[pay_col].fillna("Cash").str.upper()
        df["IsDigital"] = df["Mode"].apply(lambda x: "Digital" if any(k in str(x) for k in digital_keys) else "Cash")
    else:
        df["IsDigital"] = "Unknown"
        
    return df

# ─────────────────────────────────────────────
# APP LAYOUT
# ─────────────────────────────────────────────
st.title("🅿️ Park 360: Easy Manager Dashboard")
st.markdown("A simple overview of your parking operations and revenue.")

uploaded_file = st.file_uploader("Step 1: Upload your Excel report", type=["xlsx"])

if uploaded_file:
    df = load_and_clean(uploaded_file)
    
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Data")
    v_types = df["Vehicleno"].nunique() # Example metric
    selected_vehicles = st.sidebar.multiselect("Vehicle Type", options=df["Vehicletype"].unique(), default=df["Vehicletype"].unique())
    df = df[df["Vehicletype"].isin(selected_vehicles)]

    # ─────────────────────────────────────────────
    # SECTION 1: THE BIG NUMBERS
    # ─────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Money Collected", f"₹{df['Amount'].sum():,.0f}")
    with col2:
        st.metric("Total Vehicles", f"{len(df):,}")
    with col3:
        # Simple Logic: Avg revenue per vehicle
        st.metric("Avg. Collection / Car", f"₹{df['Amount'].mean():.2f}")
    with col4:
        # Digital %
        dig_pct = (df[df["IsDigital"] == "Digital"].shape[0] / len(df)) * 100
        st.metric("Digital Payment %", f"{dig_pct:.1f}%")

    st.divider()

    # ─────────────────────────────────────────────
    # SECTION 2: PEAK TIMES (WHEN IS IT BUSY?)
    # ─────────────────────────────────────────────
    st.subheader("⏰ When are customers arriving?")
    hourly_data = df.groupby("Hour").size().reset_index(name="Count")
    
    # Simplify: Use a bar chart for peak hours instead of a complex heatmap
    fig_peaks = px.bar(
        hourly_data, x="Hour", y="Count",
        labels={"Count": "Number of Vehicles", "Hour": "Time of Day (24hr)"},
        color_discrete_sequence=["#1e3d59"]
    )
    fig_peaks.update_layout(bargap=0.2)
    st.plotly_chart(fig_peaks, use_container_width=True)

    # ─────────────────────────────────────────────
    # SECTION 3: REVENUE & PAYMENTS
    # ─────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("💰 Revenue by Vehicle Type")
        rev_v = df.groupby("Vehicletype")["Amount"].sum().reset_index()
        fig_rev = px.pie(rev_v, values="Amount", names="Vehicletype", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_b:
        st.subheader("💳 Cash vs Digital")
        pay_split = df["IsDigital"].value_counts().reset_index()
        pay_split.columns = ["Type", "Total"]
        fig_pay = px.bar(pay_split, x="Type", y="Total", color="Type",
                         color_discrete_map={"Digital": "#2ecc71", "Cash": "#e74c3c"})
        st.plotly_chart(fig_pay, use_container_width=True)

    st.divider()

    # ─────────────────────────────────────────────
    # SECTION 4: OPERATOR PERFORMANCE (SIMPLIFIED)
    # ─────────────────────────────────────────────
    st.subheader("👤 Staff Performance (Operator)")
    op_col = "Extra Inuser" if "Extra Inuser" in df.columns else None
    
    if op_col:
        op_perf = df.groupby(op_col).agg({
            "Amount": "sum",
            "Vehicleno": "count"
        }).rename(columns={"Amount": "Total Revenue", "Vehicleno": "Vehicles Handled"}).reset_index()
        
        # Sort by most revenue
        op_perf = op_perf.sort_values("Total Revenue", ascending=False)
        st.table(op_perf) # Tables are often easier for managers than complex multi-axis charts
    else:
        st.info("Operator information not found in this file.")

    # ─────────────────────────────────────────────
    # SECTION 5: DAILY TREND
    # ─────────────────────────────────────────────
    st.subheader("📅 Daily Business Trend")
    daily_trend = df.groupby("Date")["Amount"].sum().reset_index()
    fig_trend = px.line(daily_trend, x="Date", y="Amount", markers=True,
                        line_shape="spline", color_discrete_sequence=["#1e3d59"])
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.info("Waiting for your Excel file to generate the report...")

