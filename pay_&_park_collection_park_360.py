import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings("ignore")

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






    # Standardise column names
    df.columns = df.columns.str.strip()

    # Parse datetimes
    for col in ["Intime", "Outtime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # Numeric amounts
    for col in ["Initial Amount", "Extra Amount", "Amount", "Ticket Loss Amount"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[₹,\s]", "", regex=True)
                .replace("nan", np.nan)
                .astype(float)
            )

    # Derived columns
    df["InDate"]       = df["Intime"].dt.date
    df["InHour"]       = df["Intime"].dt.hour
    df["DayOfWeek"]    = df["Intime"].dt.day_name()
    df["IsWeekend"]    = df["Intime"].dt.dayofweek >= 5
    df["DayType"]      = df["IsWeekend"].map({True: "Weekend", False: "Weekday"})

    # Operator = Extra Inuser (entry operator)
    if "Extra Inuser" in df.columns:
        df["Operator"] = df["Extra Inuser"].fillna("Unknown").str.strip()

    # Payment mode from Extra Paymenttype C
    if "Extra Paymenttype C" in df.columns:
        df["PaymentMode"] = df["Extra Paymenttype C"].fillna("Unknown").str.upper().str.strip()
    else:
        df["PaymentMode"] = "Unknown"

    # Digital flag
    digital_modes = {"UPI", "CARD", "FASTAG", "ONLINE"}
    df["IsDigital"] = df["PaymentMode"].apply(
        lambda x: any(d in str(x) for d in digital_modes)
    )

    return df


# ─────────────────────────────────────────────
# 1.  INTIME / OUTTIME  ANALYSIS
# ─────────────────────────────────────────────

def analysis_intime_outtime(df: pd.DataFrame) -> dict:
    """
    • Hourly vehicle count split by Weekday/Weekend
    • Hourly vehicle count split by Operator
    • Peak hours (top 3 hours by volume)
    """
    results = {}

    # Hourly totals
    hourly = (
        df.groupby(["InHour", "DayType"])
        .size()
        .reset_index(name="VehicleCount")
    )
    results["hourly_by_daytype"] = hourly

    # Operator x Hour heatmap data
    if "Operator" in df.columns:
        op_hour = (
            df.groupby(["Operator", "InHour"])
            .size()
            .reset_index(name="VehicleCount")
        )
        results["operator_hour"] = op_hour

    # Peak hours
    peak = (
        df.groupby("InHour")
        .size()
        .reset_index(name="VehicleCount")
        .sort_values("VehicleCount", ascending=False)
        .head(3)
    )
    results["peak_hours"] = peak

    # Busy time windows (0-6 Night, 6-12 Morning, 12-18 Afternoon, 18-24 Evening)
    bins   = [0, 6, 12, 18, 24]
    labels = ["Night (0-6)", "Morning (6-12)", "Afternoon (12-18)", "Evening (18-24)"]
    df["TimeWindow"] = pd.cut(df["InHour"], bins=bins, labels=labels, right=False)
    window = df.groupby(["TimeWindow", "DayType"]).size().reset_index(name="VehicleCount")
    results["time_window"] = window

    return results


# ─────────────────────────────────────────────
# 2.  7-DAY TREND ANALYSIS
# ─────────────────────────────────────────────

def analysis_7day_trend(df: pd.DataFrame) -> dict:
    """
    • Daily transaction count + revenue
    • 7-day rolling average
    • Variance from average
    • Anomaly detection (±1.5 σ)
    """
    results = {}

    daily = (
        df.groupby("InDate")
        .agg(
            Transactions=("Vehicleno", "count"),
            Revenue=("Amount", "sum"),
        )
        .reset_index()
        .sort_values("InDate")
    )

    daily["Transactions_7dMA"] = daily["Transactions"].rolling(7, min_periods=1).mean()
    daily["Revenue_7dMA"]      = daily["Revenue"].rolling(7, min_periods=1).mean()

    avg_tx  = daily["Transactions"].mean()
    std_tx  = daily["Transactions"].std()
    avg_rev = daily["Revenue"].mean()
    std_rev = daily["Revenue"].std()

    daily["Tx_VarFromAvg"]  = daily["Transactions"] - avg_tx
    daily["Rev_VarFromAvg"] = daily["Revenue"] - avg_rev

    daily["Tx_Anomaly"]  = daily["Transactions"].apply(
        lambda x: "Spike" if x > avg_tx + 1.5 * std_tx
        else ("Drop" if x < avg_tx - 1.5 * std_tx else "Normal")
    )
    daily["Rev_Anomaly"] = daily["Revenue"].apply(
        lambda x: "Spike" if x > avg_rev + 1.5 * std_rev
        else ("Drop" if x < avg_rev - 1.5 * std_rev else "Normal")
    )

    # WoW growth (needs 7+ days)
    if len(daily) >= 7:
        daily["Tx_WoW_Growth"]  = daily["Transactions"].pct_change(7) * 100
        daily["Rev_WoW_Growth"] = daily["Revenue"].pct_change(7) * 100

    results["daily_trend"] = daily
    return results


# ─────────────────────────────────────────────
# 3.  DAY-WISE PERFORMANCE
# ─────────────────────────────────────────────

def analysis_daywise_performance(df: pd.DataFrame) -> dict:
    """
    Compare each day's collection to the average of the same weekday
    over the last 7 occurrences. Tag as Overperforming / Stable / Underperforming.
    """
    results = {}

    daily = (
        df.groupby(["InDate", "DayOfWeek"])
        .agg(Revenue=("Amount", "sum"), Transactions=("Vehicleno", "count"))
        .reset_index()
        .sort_values("InDate")
    )

    def classify(row, avg_col, threshold=0.10):
        if row["Revenue"] > row[avg_col] * (1 + threshold):
            return "Overperforming"
        elif row["Revenue"] < row[avg_col] * (1 - threshold):
            return "Underperforming"
        else:
            return "Stable"

    # For each row, compute avg of same weekday in last 7 occurrences
    records = []
    for idx, row in daily.iterrows():
        same_day = daily[
            (daily["DayOfWeek"] == row["DayOfWeek"]) & (daily["InDate"] < row["InDate"])
        ].tail(7)
        avg_rev = same_day["Revenue"].mean() if not same_day.empty else row["Revenue"]
        records.append(avg_rev)

    daily["Avg_SameWeekday_Rev"] = records
    daily["Performance_Tag"] = daily.apply(
        lambda r: classify(r, "Avg_SameWeekday_Rev"), axis=1
    )

    results["daywise"] = daily
    return results


# ─────────────────────────────────────────────
# 4.  OPERATOR PERFORMANCE
# ─────────────────────────────────────────────

def analysis_operator_performance(df: pd.DataFrame) -> dict:
    """
    • Rank operators by avg daily revenue (consistency metric)
    • Digital vs Cash split per operator
    """
    results = {}

    if "Operator" not in df.columns:
        return results

    op_daily = (
        df.groupby(["Operator", "InDate"])
        .agg(Revenue=("Amount", "sum"), Transactions=("Vehicleno", "count"))
        .reset_index()
    )

    op_summary = (
        op_daily.groupby("Operator")
        .agg(
            AvgDailyRevenue=("Revenue", "mean"),
            AvgDailyTx=("Transactions", "mean"),
            StdDailyRevenue=("Revenue", "std"),
            TotalDays=("InDate", "nunique"),
        )
        .reset_index()
    )

    # Consistency score = avg / std  (lower std relative to mean → more consistent)
    op_summary["ConsistencyScore"] = (
        op_summary["AvgDailyRevenue"] /
        op_summary["StdDailyRevenue"].replace(0, 1)
    ).round(2)
    op_summary = op_summary.sort_values("ConsistencyScore", ascending=False)

    # Payment mode split
    digital_modes = {"UPI", "CARD", "FASTAG", "ONLINE"}
    op_pay = (
        df.groupby(["Operator", "PaymentMode"])
        .size()
        .reset_index(name="TxCount")
    )
    op_pay["IsDigital"] = op_pay["PaymentMode"].apply(
        lambda x: any(d in str(x) for d in digital_modes)
    )
    op_digital = (
        op_pay.groupby(["Operator", "IsDigital"])["TxCount"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    op_digital.columns.name = None
    if True in op_digital.columns and False in op_digital.columns:
        op_digital.rename(columns={True: "Digital_Tx", False: "Cash_Tx"}, inplace=True)
        op_digital["Digital_Pct"] = (
            op_digital["Digital_Tx"] /
            (op_digital["Digital_Tx"] + op_digital["Cash_Tx"]) * 100
        ).round(1)

    results["operator_summary"] = op_summary
    results["operator_digital"] = op_digital
    return results


# ─────────────────────────────────────────────
# 5.  PAYMENT MODE INSIGHTS
# ─────────────────────────────────────────────

def analysis_payment_modes(df: pd.DataFrame) -> dict:
    """
    • Daily trend per payment mode
    • Digital adoption % over time
    • Operators / locations with high cash usage
    """
    results = {}

    # Daily mode trend
    daily_mode = (
        df.groupby(["InDate", "PaymentMode"])
        .agg(TxCount=("Vehicleno", "count"), Revenue=("Amount", "sum"))
        .reset_index()
        .sort_values("InDate")
    )
    results["daily_mode_trend"] = daily_mode

    # Digital adoption % per day
    daily_digital = (
        df.groupby("InDate")
        .agg(
            Total=("Vehicleno", "count"),
            Digital=("IsDigital", "sum"),
        )
        .reset_index()
    )
    daily_digital["DigitalAdoptionPct"] = (
        daily_digital["Digital"] / daily_digital["Total"] * 100
    ).round(1)
    results["digital_adoption"] = daily_digital

    # Operator cash usage (if available)
    if "Operator" in df.columns:
        cash_mask = ~df["IsDigital"]
        op_cash = (
            df[cash_mask]
            .groupby("Operator")
            .size()
            .reset_index(name="CashTx")
            .sort_values("CashTx", ascending=False)
        )
        results["operator_cash"] = op_cash

    return results


# ─────────────────────────────────────────────
# VISUALISATION
# ─────────────────────────────────────────────

COLORS = {
    "primary":   "#1A73E8",
    "secondary": "#34A853",
    "accent":    "#FBBC04",
    "danger":    "#EA4335",
    "bg":        "#F8F9FA",
    "dark":      "#202124",
    "panel":     "#FFFFFF",
    "grid":      "#E0E0E0",
}

def _style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(COLORS["bg"])
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.6, zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.tick_params(colors=COLORS["dark"], labelsize=8)
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold",
                     color=COLORS["dark"], pad=8)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8, color=COLORS["dark"])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8, color=COLORS["dark"])


def plot_all(df: pd.DataFrame, save_path: str = "parking_dashboard.png"):
    r1 = analysis_intime_outtime(df)
    r2 = analysis_7day_trend(df)
    r3 = analysis_daywise_performance(df)
    r4 = analysis_operator_performance(df)
    r5 = analysis_payment_modes(df)

    fig = plt.figure(figsize=(22, 28), facecolor=COLORS["bg"])
    fig.suptitle("Parking / Toll Analytics Dashboard",
                 fontsize=18, fontweight="bold", color=COLORS["dark"], y=0.99)

    gs = gridspec.GridSpec(5, 2, figure=fig, hspace=0.55, wspace=0.35,
                           top=0.96, bottom=0.03, left=0.06, right=0.97)

    # ── 1a. Hourly vehicle count (weekday vs weekend) ──────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    hourly = r1.get("hourly_by_daytype", pd.DataFrame())
    if not hourly.empty:
        for dtype, color in [("Weekday", COLORS["primary"]),
                             ("Weekend", COLORS["accent"])]:
            sub = hourly[hourly["DayType"] == dtype]
            ax1.plot(sub["InHour"], sub["VehicleCount"],
                     marker="o", label=dtype, color=color, linewidth=2)
        ax1.legend(fontsize=8)
    _style_ax(ax1, "Hourly Traffic: Weekday vs Weekend", "Hour of Day", "Vehicles")
    ax1.xaxis.set_major_locator(mticker.MultipleLocator(2))

    # ── 1b. Time-window load ───────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    tw = r1.get("time_window", pd.DataFrame())
    if not tw.empty:
        pivot = tw.pivot(index="TimeWindow", columns="DayType", values="VehicleCount").fillna(0)
        pivot.plot(kind="bar", ax=ax2, color=[COLORS["primary"], COLORS["accent"]],
                   width=0.6, edgecolor="white", zorder=3)
        ax2.set_xticklabels(pivot.index, rotation=15, ha="right")
        ax2.legend(fontsize=8)
    _style_ax(ax2, "Busy Time Windows (Transaction Load)", "Time Window", "Vehicles")

    # ── 2a. 7-Day Transaction Trend ────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    daily = r2.get("daily_trend", pd.DataFrame())
    if not daily.empty:
        dates = range(len(daily))
        ax3.bar(dates, daily["Transactions"], color=COLORS["primary"],
                alpha=0.5, zorder=3, label="Daily Tx")
        ax3.plot(dates, daily["Transactions_7dMA"], color=COLORS["danger"],
                 linewidth=2, label="7-day MA")

        # Mark anomalies
        for i, row in daily.iterrows():
            idx = list(daily.index).index(i)
            if row["Tx_Anomaly"] == "Spike":
                ax3.annotate("▲", (idx, row["Transactions"]),
                             color=COLORS["secondary"], fontsize=9, ha="center")
            elif row["Tx_Anomaly"] == "Drop":
                ax3.annotate("▼", (idx, row["Transactions"]),
                             color=COLORS["danger"], fontsize=9, ha="center")

        ax3.set_xticks(dates)
        ax3.set_xticklabels(
            [str(d) for d in daily["InDate"]], rotation=30, ha="right", fontsize=7
        )
        ax3.legend(fontsize=8)
    _style_ax(ax3, "7-Day Transaction Trend (▲Spike ▼Drop)", "Date", "Transactions")

    # ── 2b. Revenue trend + variance bar ──────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    if not daily.empty:
        dates = range(len(daily))
        ax4.plot(dates, daily["Revenue"], color=COLORS["secondary"],
                 linewidth=2, marker="o", markersize=4, label="Revenue")
        ax4.plot(dates, daily["Revenue_7dMA"], color=COLORS["primary"],
                 linewidth=1.5, linestyle="--", label="7-day MA")
        # Variance fill
        ax4.fill_between(dates, daily["Revenue"], daily["Revenue_7dMA"],
                         where=(daily["Revenue"] >= daily["Revenue_7dMA"]),
                         interpolate=True, color=COLORS["secondary"], alpha=0.15,
                         label="Above avg")
        ax4.fill_between(dates, daily["Revenue"], daily["Revenue_7dMA"],
                         where=(daily["Revenue"] < daily["Revenue_7dMA"]),
                         interpolate=True, color=COLORS["danger"], alpha=0.15,
                         label="Below avg")
        ax4.set_xticks(dates)
        ax4.set_xticklabels(
            [str(d) for d in daily["InDate"]], rotation=30, ha="right", fontsize=7
        )
        ax4.legend(fontsize=8)
    _style_ax(ax4, "Revenue Trend vs 7-Day Average", "Date", "Revenue (₹)")

    # ── 3. Day-wise Performance Tags ──────────────────────────────────────
    ax5 = fig.add_subplot(gs[2, 0])
    dw = r3.get("daywise", pd.DataFrame())
    tag_colors = {
        "Overperforming":  COLORS["secondary"],
        "Stable":          COLORS["primary"],
        "Underperforming": COLORS["danger"],
    }
    if not dw.empty:
        dw_plot = dw.tail(30)
        x = range(len(dw_plot))
        colors = [tag_colors.get(t, COLORS["primary"]) for t in dw_plot["Performance_Tag"]]
        ax5.bar(x, dw_plot["Revenue"], color=colors, zorder=3, width=0.7)
        ax5.plot(x, dw_plot["Avg_SameWeekday_Rev"], color=COLORS["dark"],
                 linewidth=1.5, linestyle="--", label="Weekday Avg")
        ax5.set_xticks(list(x))
        ax5.set_xticklabels(
            [str(d) for d in dw_plot["InDate"]], rotation=35, ha="right", fontsize=6.5
        )
        # Legend patches
        from matplotlib.patches import Patch
        handles = [Patch(color=c, label=l) for l, c in tag_colors.items()]
        handles.append(plt.Line2D([0], [0], color=COLORS["dark"],
                                  linestyle="--", label="Weekday Avg"))
        ax5.legend(handles=handles, fontsize=7, loc="upper left")
    _style_ax(ax5, "Day-wise Performance vs Same-Weekday Avg", "Date", "Revenue (₹)")

    # ── 3b. Performance tag distribution pie ──────────────────────────────
    ax6 = fig.add_subplot(gs[2, 1])
    if not dw.empty:
        tag_counts = dw["Performance_Tag"].value_counts()
        colors_pie = [tag_colors.get(t, "#999") for t in tag_counts.index]
        ax6.pie(tag_counts, labels=tag_counts.index, colors=colors_pie,
                autopct="%1.1f%%", startangle=140,
                textprops={"fontsize": 9, "color": COLORS["dark"]},
                wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    _style_ax(ax6, "Performance Tag Distribution")

    # ── 4a. Operator Consistency Ranking ──────────────────────────────────
    ax7 = fig.add_subplot(gs[3, 0])
    op_sum = r4.get("operator_summary", pd.DataFrame())
    if not op_sum.empty:
        top = op_sum.head(10)
        ax7.barh(top["Operator"], top["AvgDailyRevenue"],
                 color=COLORS["primary"], zorder=3)
        ax7.set_xlabel("Avg Daily Revenue (₹)", fontsize=8)
        ax7.invert_yaxis()
    _style_ax(ax7, "Operator Ranking by Avg Daily Revenue", "Revenue (₹)", "Operator")

    # ── 4b. Digital vs Cash per operator ──────────────────────────────────
    ax8 = fig.add_subplot(gs[3, 1])
    op_dig = r4.get("operator_digital", pd.DataFrame())
    if not op_dig.empty and "Digital_Pct" in op_dig.columns:
        top_d = op_dig.sort_values("Digital_Pct", ascending=False).head(10)
        bars = ax8.barh(top_d["Operator"], top_d["Digital_Pct"],
                        color=COLORS["secondary"], zorder=3, label="Digital %")
        ax8.axvline(50, color=COLORS["danger"], linewidth=1.2,
                    linestyle="--", label="50% threshold")
        ax8.set_xlim(0, 105)
        for bar, val in zip(bars, top_d["Digital_Pct"]):
            ax8.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                     f"{val:.1f}%", va="center", fontsize=7, color=COLORS["dark"])
        ax8.invert_yaxis()
        ax8.legend(fontsize=8)
    _style_ax(ax8, "Digital Payment % by Operator", "Digital Adoption (%)", "Operator")

    # ── 5. Payment Mode Trend over time ───────────────────────────────────
    ax9 = fig.add_subplot(gs[4, 0])
    dm = r5.get("daily_mode_trend", pd.DataFrame())
    if not dm.empty:
        pivot_dm = dm.pivot_table(
            index="InDate", columns="PaymentMode", values="TxCount", aggfunc="sum"
        ).fillna(0)
        # Limit to top-5 modes
        top_modes = pivot_dm.sum().nlargest(5).index
        pivot_dm = pivot_dm[top_modes]
        mode_colors = [
            COLORS["primary"], COLORS["secondary"], COLORS["accent"],
            COLORS["danger"], "#9C27B0"
        ]
        pivot_dm.plot(kind="area", ax=ax9, color=mode_colors[:len(top_modes)],
                      alpha=0.6, stacked=True)
        ax9.set_xticklabels(
            [str(d) for d in pivot_dm.index], rotation=30, ha="right", fontsize=7
        )
        ax9.legend(fontsize=7, loc="upper left")
    _style_ax(ax9, "Payment Mode Trend (Stacked)", "Date", "Transactions")

    # ── 5b. Digital Adoption % KPI line ───────────────────────────────────
    ax10 = fig.add_subplot(gs[4, 1])
    da = r5.get("digital_adoption", pd.DataFrame())
    if not da.empty:
        x = range(len(da))
        ax10.fill_between(x, da["DigitalAdoptionPct"], alpha=0.2,
                          color=COLORS["secondary"])
        ax10.plot(x, da["DigitalAdoptionPct"], color=COLORS["secondary"],
                  linewidth=2, marker="o", markersize=4)
        ax10.axhline(50, color=COLORS["danger"], linestyle="--",
                     linewidth=1, label="50% target")
        ax10.set_ylim(0, 105)
        ax10.set_xticks(list(x))
        ax10.set_xticklabels(
            [str(d) for d in da["InDate"]], rotation=30, ha="right", fontsize=7
        )
        ax10.legend(fontsize=8)
    _style_ax(ax10, "Digital Adoption % (KPI Trend)", "Date", "Digital %")

    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    print(f"[✓] Dashboard saved → {save_path}")
    return fig


# ─────────────────────────────────────────────
# MAIN REPORT PRINTER
# ─────────────────────────────────────────────

def print_summary_report(df: pd.DataFrame):
    r1 = analysis_intime_outtime(df)
    r2 = analysis_7day_trend(df)
    r3 = analysis_daywise_performance(df)
    r4 = analysis_operator_performance(df)
    r5 = analysis_payment_modes(df)

    sep = "─" * 60

    print(f"\n{'═'*60}")
    print("  PARKING / TOLL ANALYTICS — SUMMARY REPORT")
    print(f"{'═'*60}")

    # 1. Peak hours
    print(f"\n{'[1] INTIME/OUTTIME ANALYSIS':}")
    print(sep)
    peak = r1.get("peak_hours", pd.DataFrame())
    if not peak.empty:
        print("  Top 3 Peak Hours:")
        for _, row in peak.iterrows():
            print(f"    Hour {int(row['InHour']):02d}:00 → {int(row['VehicleCount'])} vehicles")

    # 2. Anomalies
    print(f"\n{'[2] 7-DAY TREND ANALYSIS':}")
    print(sep)
    daily = r2.get("daily_trend", pd.DataFrame())
    if not daily.empty:
        spikes = daily[daily["Tx_Anomaly"] == "Spike"]
        drops  = daily[daily["Tx_Anomaly"] == "Drop"]
        print(f"  Avg Daily Transactions : {daily['Transactions'].mean():.1f}")
        print(f"  Avg Daily Revenue      : ₹{daily['Revenue'].mean():,.2f}")
        if not spikes.empty:
            print(f"  ⚡ Spike days : {', '.join(map(str, spikes['InDate'].tolist()))}")
        if not drops.empty:
            print(f"  ⚠ Drop days  : {', '.join(map(str, drops['InDate'].tolist()))}")

    # 3. Performance tags
    print(f"\n{'[3] DAY-WISE PERFORMANCE':}")
    print(sep)
    dw = r3.get("daywise", pd.DataFrame())
    if not dw.empty:
        tag_summary = dw["Performance_Tag"].value_counts()
        for tag, cnt in tag_summary.items():
            print(f"  {tag:<20} : {cnt} day(s)")

    # 4. Operators
    print(f"\n{'[4] OPERATOR PERFORMANCE':}")
    print(sep)
    op_sum = r4.get("operator_summary", pd.DataFrame())
    if not op_sum.empty:
        print("  Top 5 operators (by consistency):")
        for _, row in op_sum.head(5).iterrows():
            print(f"    {row['Operator']:<25} Avg Rev: ₹{row['AvgDailyRevenue']:>8,.2f}  "
                  f"Consistency: {row['ConsistencyScore']:.2f}")
    op_dig = r4.get("operator_digital", pd.DataFrame())
    if not op_dig.empty and "Digital_Pct" in op_dig.columns:
        low_digital = op_dig[op_dig["Digital_Pct"] < 30].sort_values("Digital_Pct")
        if not low_digital.empty:
            print("\n  ⚠  Low digital adoption operators (< 30%):")
            for _, row in low_digital.iterrows():
                print(f"    {row['Operator']:<25} Digital: {row['Digital_Pct']:.1f}%")

    # 5. Digital KPI
    print(f"\n{'[5] PAYMENT MODE INSIGHTS':}")
    print(sep)
    da = r5.get("digital_adoption", pd.DataFrame())
    if not da.empty:
        print(f"  Overall Digital Adoption : {da['DigitalAdoptionPct'].mean():.1f}%")
        latest = da.iloc[-1]
        print(f"  Latest day adoption      : {latest['DigitalAdoptionPct']:.1f}%")

    print(f"\n{'═'*60}\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parking_analytics.py <data_file.csv|xlsx>")
        print("\nRunning with DEMO synthetic data …\n")

        # ── Generate synthetic demo data ──
        np.random.seed(42)
        n = 500
        base = pd.Timestamp("2026-02-20")
        in_times = [
            base + pd.Timedelta(days=int(np.random.randint(0, 14)),
                                hours=int(np.random.choice(
                                    [7,8,9,10,11,12,13,14,15,16,17,18,19,20],
                                    p=[.04,.08,.10,.09,.08,.08,.07,.07,.08,.07,.08,.09,.09,.08]
                                )),
                                minutes=int(np.random.randint(0, 60)))
            for _ in range(n)
        ]
        out_times = [t + pd.Timedelta(minutes=int(np.random.randint(5, 120)))
                     for t in in_times]

        operators = np.random.choice(
            ["FASTag Based Automated Entry", "Operator 1", "Operator 2",
             "Operator 3", "Operator 4"],
            size=n, p=[0.4, 0.2, 0.2, 0.1, 0.1]
        )
        pay_modes = np.random.choice(
            ["FASTAG", "CASH", "UPI", "CARD"],
            size=n, p=[0.35, 0.30, 0.25, 0.10]
        )
        amounts = np.where(pay_modes == "CASH",
                           np.random.choice([20, 40, 60, 80, 100], size=n),
                           np.random.choice([20, 40, 60, 80, 100], size=n))

        demo_df = pd.DataFrame({
            "Vehicleno":          [f"VH{i:04d}" for i in range(n)],
            "Utcno":              [f"UTC{i:06d}" for i in range(n)],
            "Vehicletype":        np.random.choice(["Car", "Truck", "Bike"], n),
            "Intime":             in_times,
            "Outtime":            out_times,
            "Initial Amount":     amounts,
            "Extra Amount":       np.random.choice([0, 10, 20], n, p=[0.8, 0.1, 0.1]),
            "Amount":             amounts,
            "Invoiceno":          np.arange(100000, 100000 + n),
            "Unique No":          np.random.randint(1e12, 9e12, n),
            "Extra Inuser":       operators,
            "Extra Outuser":      np.random.choice(
                                      ["FASTag Based Automated Exit", "Operator 4",
                                       "Operator 5"], n),
            "Extra Paymenttype C": pay_modes,
            "Extra Transactionid Ou": [f"TXN{i:010d}" for i in range(n)],
            "Paymentstatus C":    np.random.choice(["Settle", "Pending"], n, p=[0.95, 0.05]),
            "Ticket Loss Amount": np.random.choice([0, 0, 0, 10, 20], n),
            "Vehicle Exit Medium": np.random.choice(["FASTAG", "Manual"], n, p=[0.6, 0.4]),
        })

        df = load_data.__wrapped__(demo_df) if hasattr(load_data, "__wrapped__") else _load_from_df(demo_df)

    else:
        df = load_data(sys.argv[1])

    print_summary_report(df)
    plot_all(df, save_path="parking_dashboard.png")


# ─────────────────────────────────────────────
# Helper for demo (bypass file path)
# ─────────────────────────────────────────────

def _load_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """Same transformations as load_data but accepts an existing DataFrame."""
    for col in ["Intime", "Outtime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["Initial Amount", "Extra Amount", "Amount", "Ticket Loss Amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["InDate"]    = df["Intime"].dt.date
    df["InHour"]    = df["Intime"].dt.hour
    df["DayOfWeek"] = df["Intime"].dt.day_name()
    df["IsWeekend"] = df["Intime"].dt.dayofweek >= 5
    df["DayType"]   = df["IsWeekend"].map({True: "Weekend", False: "Weekday"})

    if "Extra Inuser" in df.columns:
        df["Operator"] = df["Extra Inuser"].fillna("Unknown").str.strip()
    if "Extra Paymenttype C" in df.columns:
        df["PaymentMode"] = df["Extra Paymenttype C"].fillna("Unknown").str.upper().str.strip()
    else:
        df["PaymentMode"] = "Unknown"

    digital_modes = {"UPI", "CARD", "FASTAG", "ONLINE"}
    df["IsDigital"] = df["PaymentMode"].apply(
        lambda x: any(d in str(x) for d in digital_modes)
    )
    return df


# patch main block to use _load_from_df for demo
import builtins
_real_main_block = None

