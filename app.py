import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Company Growth AI Agent",
    page_icon="📈",
    layout="wide"
)

# ---------------- GROQ CONFIG ----------------
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_ai(prompt):
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ Groq API key not found. Add it in Streamlit Secrets."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are a senior business analyst."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 400
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return f"⚠️ GROQ API error: {response.text}"
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

# ---------------- PDF GENERATOR ----------------
def generate_pdf(avg_growth, best_rev, worst_rev, avg_rev, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Company Growth Report", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Average Growth (%): {avg_growth:.2f}", ln=True)
    pdf.cell(0, 8, f"Best Revenue: {best_rev:,.0f}", ln=True)
    pdf.cell(0, 8, f"Worst Revenue: {worst_rev:,.0f}", ln=True)
    pdf.cell(0, 8, f"Average Revenue: {avg_rev:,.0f}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Executive Summary (AI)", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, summary)

    return pdf.output(dest="S").encode("latin-1")

# ---------------- UI ----------------
st.title("📊 Company Growth AI Agent")
st.caption("AI-powered business analytics & forecasting")

file = st.file_uploader("Upload company CSV", type="csv")
question = st.text_input("Ask a business question (optional)")

if not file:
    st.info("⬆️ Upload a CSV file to begin analysis")
    st.stop()

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

# ---------------- CHARTS ----------------
st.line_chart(df.set_index(date_col)[revenue_col])
st.line_chart(df.set_index(date_col)["Growth (%)"])

# ---------------- AI SUMMARY ----------------
st.markdown("## 🧠 Executive Summary (AI)")

summary_prompt = f"""
Revenue history: {df[revenue_col].tolist()}
Growth rates: {df['Growth (%)'].round(2).tolist()}
Average growth: {avg_growth:.2f}%

User question: {question if question else "Provide business insights"}
"""

with st.spinner("Generating AI insights..."):
    executive_summary = ask_ai(summary_prompt)

st.markdown(executive_summary)

# ---------------- PDF DOWNLOAD ----------------
st.markdown("## ⬇️ Download Report")

safe_summary = executive_summary.encode("latin-1", "ignore").decode("latin-1")

pdf_bytes = generate_pdf(
    avg_growth,
    best_rev,
    worst_rev,
    avg_rev,
    safe_summary
)

st.download_button(
    "📄 Download Executive Report (PDF)",
    pdf_bytes,
    "company_growth_report.pdf",
    "application/pdf"
)
