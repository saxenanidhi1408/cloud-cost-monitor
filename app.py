"""
Cloud Cost Analysis and Budget Monitoring Tool
Run:  streamlit run app.py
"""
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Cloud Cost Monitor", layout="wide")

CATEGORY_MAP = {
    "EC2": "Compute", "Lambda": "Compute",
    "S3": "Storage", "EBS": "Storage",
    "RDS": "Database", "DynamoDB": "Database",
    "VPC": "Network", "CloudFront": "Network",
}


@st.cache_data
def make_mock_data(days=60, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-09-01", periods=days)
    rows = []
    for d in dates:
        for service in CATEGORY_MAP:
            rows.append((d, service, rng.uniform(5, 40)))
    df = pd.DataFrame(rows, columns=["date", "service", "cost"])
    for day_index in (20, 41):
        mask = df["date"] == dates[day_index]
        df.loc[mask & (df["service"] == "EC2"), "cost"] += 300
    return df


def load_data(uploaded):
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        df.columns = [c.strip().lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
        df = df.dropna(subset=["date", "cost"])
        return df
    return make_mock_data()


def add_category(df):
    df = df.copy()
    df["category"] = df["service"].map(CATEGORY_MAP).fillna("Other")
    return df


def detect_anomalies(daily, window, threshold, method="Z-score", pct=50.0):
    """Z-score: z = (today - rolling mean) / rolling std, flag if z > threshold.
    Moving average: deviation % = (today - rolling mean) / rolling mean * 100.
    shift(1) means only PAST days are used, so a spike cannot hide itself."""
    mean = daily.rolling(window).mean().shift(1)
    std = daily.rolling(window).std().shift(1)
    z = (daily - mean) / std
    dev = (daily - mean) / mean * 100
    out = pd.DataFrame({"cost": daily, "rolling_mean": mean,
                        "z_score": z, "deviation_%": dev})
    if method == "Z-score":
        out["is_anomaly"] = out["z_score"] > threshold
    else:
        out["is_anomaly"] = out["deviation_%"] > pct
    return out


def monthly_budget_table(df, budget):
    monthly = df.groupby(df["date"].dt.to_period("M"))["cost"].sum().reset_index()
    monthly["date"] = monthly["date"].astype(str)
    monthly.columns = ["month", "actual"]
    monthly["budget"] = budget
    monthly["used_%"] = (monthly["actual"] / budget * 100).round(1)
    monthly["status"] = np.where(monthly["actual"] > budget, "OVER BUDGET", "OK")
    return monthly


# ---------------- DASHBOARD ----------------
st.title("Cloud Cost Analysis and Budget Monitoring Tool")

with st.sidebar:
    st.header("Settings")
    uploaded = st.file_uploader("Billing CSV (date, service, cost)", type="csv")
    budget = st.number_input("Monthly budget", min_value=1.0, value=5000.0, step=100.0)
    window = st.slider("Rolling window (days)", 3, 14, 7)
    method = st.radio("Anomaly method", ["Z-score", "Moving average"])
    threshold = st.slider("Z-score threshold", 1.0, 4.0, 2.0, 0.1)
    pct = st.slider("Moving-average deviation (%)", 10, 200, 50, 5)
    st.caption("No file uploaded = mock data is used.")

df = add_category(load_data(uploaded))
daily = df.groupby("date")["cost"].sum()
result = detect_anomalies(daily, window, threshold, method, pct)
budget_df = monthly_budget_table(df, budget)

c1, c2, c3 = st.columns(3)
c1.metric("Total spend", f"{df['cost'].sum():,.2f}")
c2.metric("Days analysed", len(daily))
c3.metric("Anomalies found", int(result["is_anomaly"].sum()))

left, right = st.columns(2)

with left:
    st.subheader("Spend by category")
    by_cat = df.groupby("category")["cost"].sum()
    fig1, ax1 = plt.subplots()
    ax1.pie(by_cat, labels=by_cat.index, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

with right:
    st.subheader("Budget vs actual (monthly)")
    fig2, ax2 = plt.subplots()
    x = np.arange(len(budget_df))
    ax2.bar(x - 0.2, budget_df["budget"], width=0.4, label="Budget")
    ax2.bar(x + 0.2, budget_df["actual"], width=0.4, label="Actual")
    ax2.set_xticks(x)
    ax2.set_xticklabels(budget_df["month"])
    ax2.legend()
    st.pyplot(fig2)
    st.dataframe(budget_df, use_container_width=True)
st.subheader("Top cost-intensive services")
top = df.groupby("service")["cost"].sum().sort_values(ascending=False).head(5)
st.bar_chart(top)
share = top.iloc[0] / df["cost"].sum() * 100
st.info(f"{top.index[0]} is the most expensive service ({share:.1f}% of total spend). "
        "Review it first for cost optimization.")
st.subheader("Daily cost trend and anomalies")
fig3, ax3 = plt.subplots(figsize=(10, 3.5))
ax3.plot(result.index, result["cost"], label="Daily cost")
ax3.plot(result.index, result["rolling_mean"], linestyle="--", label=f"{window}-day mean")
flagged = result[result["is_anomaly"]]
ax3.scatter(flagged.index, flagged["cost"], color="red", zorder=5, label="Anomaly")
ax3.legend()
st.pyplot(fig3)

st.subheader("Anomaly table")
if flagged.empty:
    st.success("No anomalies detected with current settings.")
else:
    st.dataframe(flagged.round(2), use_container_width=True)


def build_html_report():
    return f"""<html><head><title>Cloud Cost Report</title></head><body>
<h1>Cloud Cost Report</h1>
<p>Total spend: {df['cost'].sum():,.2f} | Method: {method} | Anomalies: {int(result['is_anomaly'].sum())}</p>
<h2>Budget vs actual</h2>{budget_df.to_html(index=False)}
<h2>Spend by category</h2>{df.groupby('category')['cost'].sum().round(2).to_frame().to_html()}
<h2>Anomalies</h2>{flagged.round(2).to_html()}
</body></html>"""


d1, d2 = st.columns(2)
d1.download_button("Download anomaly report (CSV)",
                   result.round(2).to_csv().encode("utf-8"),
                   file_name="anomaly_report.csv", mime="text/csv")
d2.download_button("Download full report (HTML)",
                   build_html_report().encode("utf-8"),
                   file_name="budget_report.html", mime="text/html")