import streamlit as st
import pandas as pd
import requests
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Company Growth AI Agent",
    page_icon="📈",
    layout="wide"
)

# ---------------- GROK (xAI) CONFIG ----------------
XAI_API_KEY = st.secrets.get("XAI_API_KEY")

XAI_URL = "https://api.x.ai/v1/chat/completions"

def ask_ai(prompt):
    if not XAI_API_KEY:
        return "❌ Grok API key not found. Please add it in Streamlit Secrets."

    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-2-latest",
        "messages": [
            {"role": "system", "content": "You are a senior business analyst."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(XAI_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"⚠️ AI Error: {e}"

# ---------------- HELPERS ----------------
def detect_columns(df):
    date_col, revenue_col = None, None
    for col in df.columns:
        c = col.lower()
        if not date_col and ("date" in c or "month" in c):
            date_col = col
        if not revenue_col and ("revenue" in c or "sales" in c):
            revenue_col = col
    return date_col, revenue_col

# ---------------- HEADER ----------------
st.title("📊 Company Growth AI Agent")
st.caption("AI-powered business analytics & forecasting")

# ---------------- INPUT ----------------
file = st.file_uploader("Upload company CSV", type="csv")
question = st.text_input("Ask a business question (optional)")

if not file:
    st.info("⬆️ Upload a CSV file to begin analysis")
    st.stop()

# ---------------- DATA ----------------
df = pd.read_csv(file)
date_col, revenue_col = detect_columns(df)

if not date_col or not revenue_col:
    st.error("❌ CSV must contain Date and Revenue/Sales columns")
    st.stop()

df[date_col] = pd.to_datetime(df[date_col])
df = df.sort_values(date_col)
df["Growth (%)"] = df[revenue_col].pct_change() * 100

# ---------------- KPIs ----------------
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

# ---------------- TABLE ----------------
st.markdown("## 📋 Growth Analysis")
st.dataframe(df[[date_col, revenue_col, "Growth (%)"]], use_container_width=True)

# ---------------- CHARTS ----------------
st.markdown("## 📈 Revenue Trend")
st.line_chart(df.set_index(date_col)[revenue_col])

st.markdown("## 📉 Growth Rate Trend")
st.line_chart(df.set_index(date_col)["Growth (%)"])

# ---------------- FORECAST ----------------
st.markdown("## 🔮 Revenue Prediction (Next 3 Periods)")
avg_delta = df[revenue_col].diff().mean()
current = df[revenue_col].iloc[-1]

future = []
for i in range(1, 4):
    current += avg_delta
    future.append({"Period": f"Next {i}", "Predicted Revenue": round(current, 2)})

st.table(pd.DataFrame(future))

# ---------------- AI SUMMARY ----------------
st.markdown("## 🧠 Executive Summary (AI)")

summary_prompt = f"""
Revenue history: {df[revenue_col].tolist()}
Growth rates: {df['Growth (%)'].round(2).tolist()}
Best revenue: {best_rev}
Worst revenue: {worst_rev}
Average growth: {avg_growth:.2f}%

User question: {question if question else "Provide executive business insights"}

Give a concise executive summary with clear recommendations.
"""

with st.spinner("Generating AI insights..."):
    executive_summary = ask_ai(summary_prompt)

st.markdown(executive_summary)
