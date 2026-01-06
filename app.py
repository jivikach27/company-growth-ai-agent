import streamlit as st
import pandas as pd
import subprocess
import numpy as np
from sklearn.linear_model import LinearRegression
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Company Growth AI Agent", layout="wide")

# ---------------- CUSTOM CSS (PREMIUM KPI CARDS) ----------------
st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #1f2933, #111827);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
    text-align: center;
}
.kpi-title {
    font-size: 14px;
    color: #9ca3af;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Company Growth AI Agent")

# ---------------- FILE UPLOAD ----------------
file = st.file_uploader("Upload company CSV", type="csv")
multi_files = st.file_uploader(
    "Upload multiple company CSVs for comparison",
    type="csv",
    accept_multiple_files=True
)

question = st.text_input("Ask a question about your business")

# ---------------- HELPERS ----------------
def detect_columns(df):
    date_col, revenue_col = None, None
    for col in df.columns:
        c = col.lower()
        if date_col is None and ("date" in c or "month" in c):
            date_col = col
        if revenue_col is None and ("revenue" in c or "sales" in c):
            revenue_col = col
    return date_col, revenue_col


def ask_ai(prompt):
    result = subprocess.run(
        ["ollama", "run", "llama3:instruct"],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore"
    )
    return result.stdout.strip()


def generate_pdf(df, summary_text):
    filename = "Business_Growth_Report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Company Growth Analysis Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%d %B %Y')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    elements.append(Paragraph(summary_text, styles["Normal"]))
    elements.append(Spacer(1, 12))

    table_data = [df.columns.tolist()] + df.round(2).values.tolist()
    table = Table(table_data)
    elements.append(table)

    doc.build(elements)
    return filename

# ---------------- SINGLE COMPANY LOGIC ----------------
if file:
    df = pd.read_csv(file)
    date_col, revenue_col = detect_columns(df)

    if date_col and revenue_col:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        df["Growth (%)"] = df[revenue_col].pct_change() * 100

        avg_growth = df["Growth (%)"].mean()
        best_revenue = df[revenue_col].max()
        worst_revenue = df[revenue_col].min()
        avg_revenue = df[revenue_col].mean()

        # ---------- PREMIUM KPI CARDS ----------
        st.subheader("📌 Key Performance Indicators")
        k1, k2, k3, k4 = st.columns(4)

        k1.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Avg Growth %</div>
            <div class="kpi-value">{avg_growth:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        k2.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Best Revenue</div>
            <div class="kpi-value">{best_revenue:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        k3.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Worst Revenue</div>
            <div class="kpi-value">{worst_revenue:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        k4.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Avg Revenue</div>
            <div class="kpi-value">{avg_revenue:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        # ---------- TABLE ----------
        st.subheader("📊 Growth Analysis")
        st.write(df[[date_col, revenue_col, "Growth (%)"]])

        # ---------- CHARTS ----------
        st.subheader("📈 Revenue Trend")
        st.line_chart(df.set_index(date_col)[revenue_col])

        st.subheader("📉 Growth Rate Trend")
        st.line_chart(df.set_index(date_col)["Growth (%)"])

        # ---------- REVENUE PREDICTION ----------
        st.subheader("🔮 Revenue Prediction (Next 3 Periods)")
        df["t"] = np.arange(len(df))
        model = LinearRegression()
        model.fit(df[["t"]], df[revenue_col])

        future_t = np.array([[len(df)], [len(df) + 1], [len(df) + 2]])
        future_revenue = model.predict(future_t)

        pred_df = pd.DataFrame({
            "Future Period": ["Next 1", "Next 2", "Next 3"],
            "Predicted Revenue": future_revenue.round(2)
        })
        st.write(pred_df)

        # ---------- FAST AI INSIGHT (BUTTON-BASED) ----------
        st.subheader("🤖 AI Insight (Fast & Optimized)")

        if st.button("🔍 Generate AI Insight") and question:
            with st.spinner("Analyzing business metrics..."):
                prompt = f"""
You are a business analyst.

Key metrics:
- Avg revenue: {avg_revenue:.0f}
- Best revenue: {best_revenue}
- Worst revenue: {worst_revenue}
- Avg growth %: {avg_growth:.2f}
- Latest growth %: {df['Growth (%)'].iloc[-1]:.2f}

Question:
{question}

Give a clear business answer in 4–6 lines.
"""
                ai_answer = ask_ai(prompt)
                st.write(ai_answer)

        # ---------- EXECUTIVE SUMMARY ----------
        st.subheader("🧠 Executive Summary (AI)")
        with st.spinner("Generating executive summary..."):
            summary_prompt = f"""
Write a short executive summary using:
- Avg revenue: {avg_revenue:.0f}
- Best revenue: {best_revenue}
- Worst revenue: {worst_revenue}
- Avg growth %: {avg_growth:.2f}
"""
            executive_summary = ask_ai(summary_prompt)
            st.write(executive_summary)

        # ---------- PDF REPORT ----------
        st.subheader("📄 Download Business Report")
        if st.button("Generate PDF Report"):
            pdf_file = generate_pdf(
                df[[date_col, revenue_col, "Growth (%)"]],
                executive_summary
            )
            with open(pdf_file, "rb") as f:
                st.download_button(
                    "📥 Download PDF",
                    f,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

    else:
        st.error("❌ Could not detect Date or Revenue column")

# ---------------- MULTI COMPANY COMPARISON ----------------
if multi_files and len(multi_files) > 1:
    st.subheader("🏢 Multi-Company Comparison")

    comparison = []
    for f in multi_files:
        temp_df = pd.read_csv(f)
        d_col, r_col = detect_columns(temp_df)
        if d_col and r_col:
            temp_df["Growth (%)"] = temp_df[r_col].pct_change() * 100
            comparison.append({
                "Company": f.name,
                "Avg Revenue": temp_df[r_col].mean(),
                "Avg Growth %": temp_df["Growth (%)"].mean()
            })

    comp_df = pd.DataFrame(comparison)
    st.write(comp_df)
