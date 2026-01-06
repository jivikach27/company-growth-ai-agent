import streamlit as st
import pandas as pd
import numpy as np
import os
import subprocess
import shutil
from datetime import timedelta

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Company Growth AI Agent",
    page_icon="📈",
    layout="wide"
)

# ---------------- HELPER FUNCTIONS ----------------
def is_ollama_available():
    return shutil.which("ollama") is not None


def ask_ai(prompt):
    # Detect Streamlit Cloud
    IS_CLOUD = os.getenv("STREAMLIT_CLOUD") == "true"

    if IS_CLOUD:
        return (
            "🧠 **Executive Summary (Preview Mode)**\n\n"
            "This app is deployed on **Streamlit Cloud**, where local AI engines "
            "(like Ollama) are not supported.\n\n"
            "### What this means:\n"
            "- Dashboards & KPIs ✅\n"
            "- Forecasting ✅\n"
            "- AI insights ❌ (cloud limitation)\n\n"
            "👉 **To enable full AI analysis:**\n"
            "1. Clone this repository\n"
            "2. Install Ollama locally\n"
            "3. Run:\n"
            "`streamlit run app.py`\n\n"
            "You’ll get instant, private AI insights 🚀"
        )

    # Local machine only
    if shutil.which("ollama") is None:
        return "❌ Ollama not found. Please install Ollama to enable AI insights."

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3:instruct"],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=60,
            errors="ignore"
        )
        return result.stdout.strip()

    except Exception as e:
        return f"⚠️ AI error: {e}"
def detect_columns(df):
    date_col, revenue_col = None, None
    for col in df.columns:
        c = col.lower()
        if date_col is None and ("date" in c or "month" in c):
            date_col = col
        if revenue_col is None and ("revenue" in c or "sales" in c):
            revenue_col = col
    return date_col, revenue_col

# ---------------- HEADER ----------------
st.title("📊 Company Growth AI Agent")
st.caption("AI-powered business analytics & forecasting")

# ---------------- FILE UPLOAD ----------------
file = st.file_uploader("Upload company CSV", type="csv")
question = st.text_input("Ask a business question (optional)")

if not file:
    st.info("⬆️ Upload a CSV file to begin analysis")
    st.stop()

# ---------------- DATA PROCESSING ----------------
df = pd.read_csv(file)
date_col, revenue_col = detect_columns(df)

if not date_col or not revenue_col:
    st.error("❌ CSV must contain Date and Revenue/Sales columns")
    st.stop()

df[date_col] = pd.to_datetime(df[date_col])
df = df.sort_values(date_col)

df["Growth (%)"] = df[revenue_col].pct_change() * 100

# ---------------- KPI CARDS ----------------
avg_growth = df["Growth (%)"].mean()
best_rev = df[revenue_col].max()
worst_rev = df[revenue_col].min()
avg_rev = df[revenue_col].mean()

st.markdown("## 📌 Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)
c1.metric("📈 Avg Growth %", f"{avg_growth:.2f}%")
c2.metric("🏆 Best Revenue", f"{best_rev:,.0f}")
c3.metric("⚠️ Worst Revenue", f"{worst_rev:,.0f}")
c4.metric("💰 Avg Revenue", f"{avg_rev:,.0f}")

# ---------------- DATA TABLE ----------------
st.markdown("## 📋 Growth Analysis")
st.dataframe(df[[date_col, revenue_col, "Growth (%)"]], use_container_width=True)

# ---------------- CHARTS ----------------
st.markdown("## 📈 Revenue Trend")
st.line_chart(df.set_index(date_col)[revenue_col])

st.markdown("## 📉 Growth Rate Trend")
st.line_chart(df.set_index(date_col)["Growth (%)"])

# ---------------- SIMPLE FORECAST ----------------
st.markdown("## 🔮 Revenue Prediction (Next 3 Periods)")

last_date = df[date_col].iloc[-1]
avg_delta = df[revenue_col].diff().mean()

future = []
current = df[revenue_col].iloc[-1]

for i in range(1, 4):
    current += avg_delta
    future.append({
        "Period": f"Next {i}",
        "Predicted Revenue": round(current, 2)
    })

future_df = pd.DataFrame(future)
st.table(future_df)

# ---------------- AI EXECUTIVE SUMMARY ----------------
st.markdown("## 🧠 Executive Summary (AI)")

summary_prompt = f"""
You are a senior business analyst.

Revenue history: {df[revenue_col].tolist()}
Growth rates: {df['Growth (%)'].round(2).tolist()}
Best revenue: {best_rev}
Worst revenue: {worst_rev}
Average growth: {avg_growth:.2f}%

User question: {question if question else "Provide business insights"}

Give a concise executive summary with recommendations.
"""

with st.spinner("Analyzing business performance..."):
    executive_summary = ask_ai(summary_prompt)

st.markdown(executive_summary)
