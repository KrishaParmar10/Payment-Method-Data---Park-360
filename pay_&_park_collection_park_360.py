import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Park 360 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
}
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #0f4c81;
    border-left: 4px solid #0f4c81;
    padding-left: 12px;
    margin: 28px 0 16px 0;
}
.tag-over  { background:#d4edda; color:#155724; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.tag-stable{ background:#fff3cd; color:#856404; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.tag-under { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.tag-spike { background:#cce5ff; color:#004085; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.tag-drop  { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.kpi-card {
    background: linear-gradient(135deg, #0f4c81 0%, #1a6bb5 100%);
    border-radius: 14px;
    padding: 18px 22px;
    color: white;
    margin-bottom: 8px;
}
.kpi-label { font-size: 0.75rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.7rem; font-weight: 800; }
.insight-box {
    background: #f0f6ff;
    border: 1px solid #b8d4f5;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
    font-size: 0.88rem;
    color: #1a3a5c;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
try:
    st.image("Park360 Logo.png", width=180)
except:
    pass

st.title("Parking Management Analytics Dashboard")

# ─────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload Parking Report Excel File", type=["xlsx"])
st.sidebar.title("Filters")

if uploaded_file is None:
    st.info("Please upload an Excel file to continue.")
    st.stop()

# ─────────────────────────────────────────────
# READ & CLEAN DATA
# ─────────────────────────────────────────────
df_raw = pd.read_excel(uploaded_file)
df_raw.columns = df_raw.columns.str.strip()

df_raw["Intime"]  = pd.to_datetime(df_raw["Intime"],  errors="coerce")
df_raw["Outtime"] = pd.to_datetime(df_raw["Outtime"], errors="coerce")

for col in ["Initial Amount", "Extra Amount", "Amount"]:
    if col in df_raw.columns:
        df_raw[col] = (
            df_raw[col].astype(str)
            .str.replace(r"[₹,\s]", "", regex=True)
            .replace("nan", np.nan)
        )
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

# Derived
df_raw["InDate"]     = df_raw["Intime"].dt.date
df_raw["InHour"]     = df_raw["Intime"].dt.hour
df_raw["DayOfWeek"]  = df_raw["Intime"].dt.day_name()
df_raw["IsWeekend"]  = df_raw["Intime"].dt.dayofweek >= 5
df_raw["DayType"]    = df_raw["IsWeekend"].map({True: "Weekend", False: "Weekday"})

# Operator column (Extra Inuser)
op_col = "Extra Inuser" if "Extra Inuser" in df_raw.columns else None
if op_col:
    df_raw["Operator"] = df_raw[op_col].fillna("Unknown").str.strip()

# Payment mode column (Extra Paymenttype C)
pay_col = "Extra Paymenttype C" if "Extra Paymenttype C" in df_raw.columns else None
if pay_col:
    df_raw["PaymentMode"] = df_raw[pay_col].fillna("Unknown").str.upper().str.strip()
else:
    df_raw["PaymentMode"] = "Unknown"

DIGITAL = {"UPI", "CARD", "FASTAG", "ONLINE"}
df_raw["IsDigital"] = df_raw["PaymentMode"].apply(
    lambda x: any(d in str(x) for d in DIGITAL)
)

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
vehicle_options = df_raw["Vehicletype"].dropna().unique() if "Vehicletype" in df_raw.columns else []
selected_vehicle = st.sidebar.multiselect("Vehicle Type", options=vehicle_options, default=vehicle_options)

pay_status_col = "Paymentstatus Out" if "Paymentstatus Out" in df_raw.columns else \
                 ("Paymentstatus C" if "Paymentstatus C" in df_raw.columns else None)

if pay_status_col:
    payment_options = df_raw[pay_status_col].dropna().unique()
    selected_payment = st.sidebar.multiselect("Payment Status", options=payment_options, default=payment_options)

min_date = df_raw["Intime"].min().date()
max_date = df_raw["Intime"].max().date()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date])

# Apply filters
df = df_raw.copy()
if len(vehicle_options):
    df = df[df["Vehicletype"].isin(selected_vehicle)]
if pay_status_col and len(payment_options):
    df = df[df[pay_status_col].isin(selected_payment)]
if len(date_range) == 2:
    df = df[(df["Intime"].dt.date >= date_range[0]) & (df["Intime"].dt.date <= date_range[1])]

if df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# ─────────────────────────────────────────────
# EXISTING SECTION — KPI CARDS
# ─────────────────────────────────────────────
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue",          f"₹{df['Amount'].sum():,.2f}")
col2.metric("Total Initial Amount",   f"₹{df['Initial Amount'].sum():,.2f}")
col3.metric("Total Extra Amount",     f"₹{df['Extra Amount'].sum():,.2f}")
col4.metric("Total Transactions",     len(df))
st.markdown("---")

# Existing charts
col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue by Vehicle Type")
    rev_vehicle = df.groupby("Vehicletype")["Amount"].sum().reset_index()
    st.plotly_chart(px.bar(rev_vehicle, x="Vehicletype", y="Amount", color="Vehicletype"), use_container_width=True)

with col2:
    st.subheader("Payment Status Distribution")
    if pay_status_col:
        pay_status = df[pay_status_col].value_counts().reset_index()
        pay_status.columns = ["Status", "Count"]
        st.plotly_chart(px.pie(pay_status, names="Status", values="Count"), use_container_width=True)

col3, col4 = st.columns(2)
df["Entry Hour"] = df["Intime"].dt.hour
df["Exit Hour"]  = df["Outtime"].dt.hour

with col3:
    st.subheader("Hourly Entries")
    entry_h = df["Entry Hour"].value_counts().sort_index()
    st.plotly_chart(px.bar(x=entry_h.index, y=entry_h.values, labels={"x":"Hour","y":"Entries"}), use_container_width=True)

with col4:
    st.subheader("Hourly Exits")
    exit_h = df["Exit Hour"].value_counts().sort_index()
    st.plotly_chart(px.bar(x=exit_h.index, y=exit_h.values, labels={"x":"Hour","y":"Exits"}), use_container_width=True)

df["Date"] = df["Intime"].dt.date
daily_tx = df.groupby("Date").size().reset_index(name="Transactions")
st.subheader("Daily Transactions")
st.plotly_chart(px.line(daily_tx, x="Date", y="Transactions"), use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
#  NEW CONDITION 1 — INTIME / OUTTIME ANALYSIS
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📍 Condition 1 · Intime / Outtime Analysis</div>', unsafe_allow_html=True)

c1a, c1b = st.columns(2)

# Peak hours — weekday vs weekend
with c1a:
    st.markdown("**Hourly Traffic: Weekday vs Weekend**")
    hourly_dw = (
        df.groupby(["InHour", "DayType"])
        .size().reset_index(name="VehicleCount")
    )
    fig_h = px.line(
        hourly_dw, x="InHour", y="VehicleCount", color="DayType",
        markers=True,
        color_discrete_map={"Weekday": "#0f4c81", "Weekend": "#f4a261"},
        labels={"InHour": "Hour of Day", "VehicleCount": "Vehicles"}
    )
    fig_h.update_layout(xaxis=dict(dtick=2), plot_bgcolor="#f8fbff")
    st.plotly_chart(fig_h, use_container_width=True)

# Busy time windows
with c1b:
    st.markdown("**Transaction Load by Time Window**")
    bins   = [0, 6, 12, 18, 24]
    labels = ["Night (0–6)", "Morning (6–12)", "Afternoon (12–18)", "Evening (18–24)"]
    df["TimeWindow"] = pd.cut(df["InHour"], bins=bins, labels=labels, right=False)
    tw = df.groupby(["TimeWindow", "DayType"]).size().reset_index(name="VehicleCount")
    fig_tw = px.bar(
        tw, x="TimeWindow", y="VehicleCount", color="DayType", barmode="group",
        color_discrete_map={"Weekday": "#0f4c81", "Weekend": "#f4a261"},
        labels={"TimeWindow": "Window", "VehicleCount": "Vehicles"}
    )
    fig_tw.update_layout(plot_bgcolor="#f8fbff")
    st.plotly_chart(fig_tw, use_container_width=True)

# Operator x Hour heatmap
if "Operator" in df.columns:
    st.markdown("**Operator × Hour Heatmap (Vehicle Count)**")
    op_hour = df.groupby(["Operator", "InHour"]).size().reset_index(name="Count")
    pivot   = op_hour.pivot(index="Operator", columns="InHour", values="Count").fillna(0)
    fig_heat = px.imshow(
        pivot, color_continuous_scale="Blues",
        labels=dict(x="Hour of Day", y="Operator", color="Vehicles"),
        aspect="auto"
    )
    fig_heat.update_layout(height=350)
    st.plotly_chart(fig_heat, use_container_width=True)

# Peak hours table
peak_hours = (
    df.groupby("InHour").size()
    .reset_index(name="VehicleCount")
    .sort_values("VehicleCount", ascending=False)
    .head(5)
    .rename(columns={"InHour": "Hour"})
)
peak_hours["Hour"] = peak_hours["Hour"].apply(lambda h: f"{h:02d}:00")
st.markdown("**Top 5 Peak Hours**")
st.dataframe(peak_hours, use_container_width=True, hide_index=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
#  NEW CONDITION 2 — 7-DAY TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Condition 2 · 7-Day Trend Analysis</div>', unsafe_allow_html=True)

daily = (
    df.groupby("Date")
    .agg(Transactions=("Vehicleno", "count"), Revenue=("Amount", "sum"))
    .reset_index().sort_values("Date")
)
daily["Tx_7dMA"]  = daily["Transactions"].rolling(7, min_periods=1).mean()
daily["Rev_7dMA"] = daily["Revenue"].rolling(7, min_periods=1).mean()

avg_tx  = daily["Transactions"].mean()
std_tx  = daily["Transactions"].std()
avg_rev = daily["Revenue"].mean()
std_rev = daily["Revenue"].std()

daily["Tx_VarFromAvg"]  = (daily["Transactions"] - avg_tx).round(1)
daily["Rev_VarFromAvg"] = (daily["Revenue"] - avg_rev).round(2)
daily["Anomaly"] = daily["Transactions"].apply(
    lambda x: "Spike" if x > avg_tx + 1.5 * std_tx
    else ("Drop" if x < avg_tx - 1.5 * std_tx else "Normal")
)

if len(daily) >= 7:
    daily["WoW_Tx_Growth"]  = daily["Transactions"].pct_change(7).mul(100).round(1)
    daily["WoW_Rev_Growth"] = daily["Revenue"].pct_change(7).mul(100).round(1)

c2a, c2b = st.columns(2)

with c2a:
    st.markdown("**Daily Transactions + 7-Day Moving Average**")
    fig_tx = go.Figure()
    fig_tx.add_trace(go.Bar(
        x=daily["Date"], y=daily["Transactions"], name="Daily Tx",
        marker_color="#90caf9", opacity=0.7
    ))
    fig_tx.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Tx_7dMA"], name="7-day MA",
        line=dict(color="#0f4c81", width=2.5)
    ))
    # Anomaly markers
    spikes = daily[daily["Anomaly"] == "Spike"]
    drops  = daily[daily["Anomaly"] == "Drop"]
    fig_tx.add_trace(go.Scatter(
        x=spikes["Date"], y=spikes["Transactions"], mode="markers",
        name="Spike", marker=dict(symbol="triangle-up", size=12, color="#2e7d32")
    ))
    fig_tx.add_trace(go.Scatter(
        x=drops["Date"], y=drops["Transactions"], mode="markers",
        name="Drop", marker=dict(symbol="triangle-down", size=12, color="#c62828")
    ))
    fig_tx.update_layout(plot_bgcolor="#f8fbff", height=320,
                         legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig_tx, use_container_width=True)

with c2b:
    st.markdown("**Revenue Trend + Variance from Average**")
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Revenue"], name="Revenue",
        fill="tozeroy", fillcolor="rgba(15,76,129,0.12)",
        line=dict(color="#0f4c81", width=2)
    ))
    fig_rev.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Rev_7dMA"], name="7-day MA",
        line=dict(color="#f4a261", width=2, dash="dash")
    ))
    fig_rev.add_hline(y=avg_rev, line_dash="dot", line_color="#aaa",
                      annotation_text=f"Avg ₹{avg_rev:,.0f}", annotation_position="top left")
    fig_rev.update_layout(plot_bgcolor="#f8fbff", height=320,
                          legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig_rev, use_container_width=True)

# Variance table
st.markdown("**Daily Variance from Average**")
var_display = daily[["Date", "Transactions", "Tx_VarFromAvg", "Revenue", "Rev_VarFromAvg", "Anomaly"]].copy()
var_display.columns = ["Date", "Transactions", "Tx Var from Avg", "Revenue (₹)", "Rev Var from Avg (₹)", "Anomaly"]

def color_anomaly(val):
    if val == "Spike":   return "background-color:#cce5ff; color:#004085"
    elif val == "Drop":  return "background-color:#f8d7da; color:#721c24"
    return ""

st.dataframe(
    var_display.style.applymap(color_anomaly, subset=["Anomaly"]),
    use_container_width=True, hide_index=True
)

# WoW growth chart
if "WoW_Tx_Growth" in daily.columns:
    st.markdown("**Week-on-Week (WoW) Transaction Growth %**")
    wow_clean = daily.dropna(subset=["WoW_Tx_Growth"])
    fig_wow = px.bar(
        wow_clean, x="Date", y="WoW_Tx_Growth",
        color=wow_clean["WoW_Tx_Growth"].apply(lambda x: "Growth" if x >= 0 else "Decline"),
        color_discrete_map={"Growth": "#2e7d32", "Decline": "#c62828"},
        labels={"WoW_Tx_Growth": "WoW Growth (%)"}
    )
    fig_wow.add_hline(y=0, line_color="black", line_width=1)
    fig_wow.update_layout(plot_bgcolor="#f8fbff", showlegend=True, height=280)
    st.plotly_chart(fig_wow, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
#  NEW CONDITION 3 — DAY-WISE PERFORMANCE
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📅 Condition 3 · Day-wise Performance</div>', unsafe_allow_html=True)

dw = (
    df.groupby(["Date", "DayOfWeek"])
    .agg(Revenue=("Amount", "sum"), Transactions=("Vehicleno", "count"))
    .reset_index().sort_values("Date")
)

# For each row compute avg of same weekday over last 7 occurrences
same_day_avgs = []
for _, row in dw.iterrows():
    hist = dw[(dw["DayOfWeek"] == row["DayOfWeek"]) & (dw["Date"] < row["Date"])].tail(7)
    same_day_avgs.append(hist["Revenue"].mean() if not hist.empty else row["Revenue"])

dw["Avg_SameWeekday"] = same_day_avgs

def tag_performance(row, threshold=0.10):
    if row["Revenue"] > row["Avg_SameWeekday"] * (1 + threshold):
        return "Overperforming"
    elif row["Revenue"] < row["Avg_SameWeekday"] * (1 - threshold):
        return "Underperforming"
    return "Stable"

dw["Performance"] = dw.apply(tag_performance, axis=1)

TAG_COLORS = {"Overperforming": "#2e7d32", "Stable": "#f4a261", "Underperforming": "#c62828"}

c3a, c3b = st.columns([2, 1])

with c3a:
    st.markdown("**Daily Revenue vs Same-Weekday Average**")
    fig_dw = go.Figure()
    for tag, color in TAG_COLORS.items():
        subset = dw[dw["Performance"] == tag]
        fig_dw.add_trace(go.Bar(
            x=subset["Date"], y=subset["Revenue"],
            name=tag, marker_color=color, opacity=0.85
        ))
    fig_dw.add_trace(go.Scatter(
        x=dw["Date"], y=dw["Avg_SameWeekday"], name="Weekday Avg",
        line=dict(color="#333", width=2, dash="dash"), mode="lines"
    ))
    fig_dw.update_layout(barmode="overlay", plot_bgcolor="#f8fbff", height=350,
                         legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig_dw, use_container_width=True)

with c3b:
    st.markdown("**Performance Distribution**")
    tag_counts = dw["Performance"].value_counts().reset_index()
    tag_counts.columns = ["Tag", "Days"]
    fig_pie = px.pie(
        tag_counts, names="Tag", values="Days",
        color="Tag", color_discrete_map=TAG_COLORS,
        hole=0.45
    )
    fig_pie.update_layout(height=350, legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig_pie, use_container_width=True)

# Performance table
st.markdown("**Day-wise Performance Table**")
perf_display = dw[["Date","DayOfWeek","Revenue","Avg_SameWeekday","Performance"]].copy()
perf_display.columns = ["Date", "Day", "Revenue (₹)", "Weekday Avg (₹)", "Performance"]
perf_display["Revenue (₹)"]     = perf_display["Revenue (₹)"].map("₹{:,.2f}".format)
perf_display["Weekday Avg (₹)"] = perf_display["Weekday Avg (₹)"].map("₹{:,.2f}".format)

def style_perf(val):
    return {
        "Overperforming": "background-color:#d4edda;color:#155724",
        "Underperforming": "background-color:#f8d7da;color:#721c24",
        "Stable": "background-color:#fff3cd;color:#856404",
    }.get(val, "")

st.dataframe(
    perf_display.style.applymap(style_perf, subset=["Performance"]),
    use_container_width=True, hide_index=True
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
#  NEW CONDITION 4 — OPERATOR PERFORMANCE
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">👤 Condition 4 · Operator Performance</div>', unsafe_allow_html=True)

if "Operator" not in df.columns:
    st.info("Operator column (Extra Inuser) not found in data.")
else:
    op_daily = (
        df.groupby(["Operator", "Date"])
        .agg(Revenue=("Amount", "sum"), Transactions=("Vehicleno", "count"))
        .reset_index()
    )
    op_summary = (
        op_daily.groupby("Operator")
        .agg(
            AvgRevenue=("Revenue", "mean"),
            AvgTx=("Transactions", "mean"),
            StdRevenue=("Revenue", "std"),
            TotalDays=("Date", "nunique"),
        )
        .reset_index()
    )
    op_summary["StdRevenue"] = op_summary["StdRevenue"].fillna(0)
    op_summary["ConsistencyScore"] = (
        op_summary["AvgRevenue"] / op_summary["StdRevenue"].replace(0, 1)
    ).round(2)
    op_summary = op_summary.sort_values("ConsistencyScore", ascending=False)

    # Payment split
    op_pay = (
        df.groupby(["Operator", "IsDigital"])
        .size().reset_index(name="TxCount")
    )
    op_pay_pivot = op_pay.pivot(index="Operator", columns="IsDigital", values="TxCount").fillna(0)
    op_pay_pivot.columns.name = None
    op_pay_pivot = op_pay_pivot.rename(columns={True: "Digital", False: "Cash"})
    if "Digital" not in op_pay_pivot.columns: op_pay_pivot["Digital"] = 0
    if "Cash"    not in op_pay_pivot.columns: op_pay_pivot["Cash"]    = 0
    op_pay_pivot["Digital_Pct"] = (
        op_pay_pivot["Digital"] / (op_pay_pivot["Digital"] + op_pay_pivot["Cash"]) * 100
    ).round(1)
    op_pay_pivot = op_pay_pivot.reset_index()

    c4a, c4b = st.columns(2)

    with c4a:
        st.markdown("**Operator Ranking by Consistency Score**")
        top_ops = op_summary.head(10)
        fig_op = px.bar(
            top_ops, x="ConsistencyScore", y="Operator", orientation="h",
            color="AvgRevenue", color_continuous_scale="Blues",
            labels={"ConsistencyScore": "Consistency Score", "AvgRevenue": "Avg Revenue"}
        )
        fig_op.update_layout(yaxis=dict(autorange="reversed"), height=360,
                             plot_bgcolor="#f8fbff")
        st.plotly_chart(fig_op, use_container_width=True)

    with c4b:
        st.markdown("**Digital Payment % by Operator**")
        op_d = op_pay_pivot.sort_values("Digital_Pct", ascending=False).head(10)
        fig_dig = px.bar(
            op_d, x="Digital_Pct", y="Operator", orientation="h",
            color="Digital_Pct", color_continuous_scale="Greens",
            labels={"Digital_Pct": "Digital %"}
        )
        fig_dig.add_vline(x=50, line_dash="dash", line_color="red",
                          annotation_text="50% target", annotation_position="top")
        fig_dig.update_layout(yaxis=dict(autorange="reversed"), height=360,
                             plot_bgcolor="#f8fbff")
        st.plotly_chart(fig_dig, use_container_width=True)

    # Stacked Cash vs Digital
    st.markdown("**Cash vs Digital Transaction Split per Operator**")
    op_stack = op_pay_pivot.melt(id_vars="Operator", value_vars=["Cash","Digital"],
                                  var_name="Mode", value_name="Transactions")
    fig_stack = px.bar(
        op_stack, x="Operator", y="Transactions", color="Mode", barmode="stack",
        color_discrete_map={"Cash": "#ef9a9a", "Digital": "#64b5f6"},
    )
    fig_stack.update_layout(plot_bgcolor="#f8fbff", height=320,
                            xaxis_tickangle=-30)
    st.plotly_chart(fig_stack, use_container_width=True)

    # Low digital adoption highlight
    low_digital = op_pay_pivot[op_pay_pivot["Digital_Pct"] < 30]
    if not low_digital.empty:
        names = ", ".join(low_digital["Operator"].tolist())
        st.markdown(
            f'<div class="insight-box">⚠️ <strong>Low digital adoption (&lt;30%):</strong> {names} '
            f'— these operators have high cash usage and are prime targets for digital push campaigns.</div>',
            unsafe_allow_html=True
        )

    # Operator summary table
    st.markdown("**Full Operator Summary**")
    ops_disp = op_summary.merge(op_pay_pivot[["Operator","Digital_Pct"]], on="Operator", how="left")
    ops_disp["AvgRevenue"] = ops_disp["AvgRevenue"].map("₹{:,.2f}".format)
    ops_disp["AvgTx"]      = ops_disp["AvgTx"].map("{:.1f}".format)
    ops_disp = ops_disp.rename(columns={
        "AvgRevenue": "Avg Daily Revenue",
        "AvgTx": "Avg Daily Tx",
        "TotalDays": "Active Days",
        "ConsistencyScore": "Consistency ↑",
        "Digital_Pct": "Digital %"
    })
    st.dataframe(ops_disp[["Operator","Avg Daily Revenue","Avg Daily Tx",
                             "Active Days","Consistency ↑","Digital %"]],
                 use_container_width=True, hide_index=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
#  NEW CONDITION 5 — PAYMENT MODE INSIGHTS
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">💳 Condition 5 · Payment Mode Insights</div>', unsafe_allow_html=True)

# Daily mode trend
daily_mode = (
    df.groupby(["Date", "PaymentMode"])
    .agg(TxCount=("Vehicleno", "count"), Revenue=("Amount", "sum"))
    .reset_index().sort_values("Date")
)
top_modes = daily_mode.groupby("PaymentMode")["TxCount"].sum().nlargest(6).index.tolist()
daily_mode_top = daily_mode[daily_mode["PaymentMode"].isin(top_modes)]

c5a, c5b = st.columns(2)

with c5a:
    st.markdown("**Daily Transaction Trend by Payment Mode**")
    fig_pm = px.area(
        daily_mode_top, x="Date", y="TxCount", color="PaymentMode",
        labels={"TxCount": "Transactions", "PaymentMode": "Mode"},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_pm.update_layout(plot_bgcolor="#f8fbff", height=320)
    st.plotly_chart(fig_pm, use_container_width=True)

with c5b:
    st.markdown("**Overall Payment Mode Share**")
    mode_share = df.groupby("PaymentMode").size().reset_index(name="Count")
    fig_share = px.pie(
        mode_share, names="PaymentMode", values="Count",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    fig_share.update_layout(height=320, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_share, use_container_width=True)

# Digital Adoption % KPI
daily_da = (
    df.groupby("Date")
    .agg(Total=("Vehicleno", "count"), Digital=("IsDigital", "sum"))
    .reset_index()
)
daily_da["DigitalPct"] = (daily_da["Digital"] / daily_da["Total"] * 100).round(1)

st.markdown("**Digital Adoption % — Daily KPI**")
fig_da = go.Figure()
fig_da.add_trace(go.Scatter(
    x=daily_da["Date"], y=daily_da["DigitalPct"],
    fill="tozeroy", fillcolor="rgba(46,125,50,0.12)",
    line=dict(color="#2e7d32", width=2.5),
    mode="lines+markers", name="Digital %"
))
fig_da.add_hline(y=50, line_dash="dash", line_color="#c62828",
                 annotation_text="50% Target", annotation_position="top left")
fig_da.update_layout(
    yaxis=dict(range=[0, 105], ticksuffix="%"),
    plot_bgcolor="#f8fbff", height=300
)
st.plotly_chart(fig_da, use_container_width=True)

# Overall digital adoption KPI callout
overall_digital_pct = daily_da["DigitalPct"].mean()
latest_digital_pct  = daily_da["DigitalPct"].iloc[-1] if not daily_da.empty else 0

col_d1, col_d2, col_d3 = st.columns(3)
col_d1.metric("Avg Digital Adoption",   f"{overall_digital_pct:.1f}%")
col_d2.metric("Latest Day Digital %",   f"{latest_digital_pct:.1f}%")
col_d3.metric("Total Digital Tx",       int(df["IsDigital"].sum()))

# Cash-heavy operators
if "Operator" in df.columns:
    st.markdown("**Operators with High Cash Usage (scope to push digital)**")
    cash_op = (
        df[~df["IsDigital"]]
        .groupby("Operator").size()
        .reset_index(name="CashTx")
        .sort_values("CashTx", ascending=False)
    )
    fig_cash = px.bar(
        cash_op.head(10), x="CashTx", y="Operator", orientation="h",
        color="CashTx", color_continuous_scale="Reds",
        labels={"CashTx": "Cash Transactions"}
    )
    fig_cash.update_layout(yaxis=dict(autorange="reversed"), height=320,
                           plot_bgcolor="#f8fbff")
    st.plotly_chart(fig_cash, use_container_width=True)

# Mode trend table (pivot)
st.markdown("**Daily Payment Mode Breakdown Table**")
pivot_mode = daily_mode_top.pivot_table(
    index="Date", columns="PaymentMode", values="TxCount", aggfunc="sum"
).fillna(0).astype(int).reset_index()
st.dataframe(pivot_mode, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:0.78rem;color:#888;font-family:DM Sans,sans-serif'>"
    "Park 360 Analytics Dashboard · Built with Streamlit & Plotly</p>",
    unsafe_allow_html=True
)
