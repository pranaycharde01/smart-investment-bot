import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# -------------------------------
# Load and clean CSV stock dataset
# -------------------------------
@st.cache_data
def load_stock_data():
    data = pd.read_csv("stock_data.csv")
    # Clean column names: strip spaces
    data.columns = data.columns.str.strip()
    # Convert numeric columns
    data["Price"] = pd.to_numeric(data["Price"], errors="coerce")
    data["Monthly_Growth"] = pd.to_numeric(data["Monthly_Growth"], errors="coerce")
    return data

data = load_stock_data()

# -------------------------------
# Fetch real-time stock prices with fallback
# -------------------------------
@st.cache_data
def fetch_realtime_prices_safe(tickers, fallback_prices):
    prices = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                prices[ticker] = hist['Close'].iloc[-1]
            else:
                prices[ticker] = fallback_prices.get(ticker, None)
        except:
            prices[ticker] = fallback_prices.get(ticker, None)
    return prices

# -------------------------------
# Suggest stocks based on budget
# -------------------------------
def suggest_stocks(data, investable_amount):
    affordable = data[data["Price"] <= investable_amount]
    top_growth = affordable.sort_values(by="Monthly_Growth", ascending=False)
    return top_growth.head(5)

# -------------------------------
# Create PDF report
# -------------------------------
def create_pdf(suggestions):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("💰 Smart Investment Report", styles["Title"]))
    story.append(Spacer(1, 20))

    summary_data = [
        ["Field", "Value"],
        ["Income", f"₹{st.session_state.income}"],
        ["Expenses", f"₹{st.session_state.expenses}"],
        ["Savings", f"₹{st.session_state.savings}"],
        ["Investable Amount", f"₹{st.session_state.investable_amount}"],
        ["Risk Level", st.session_state.risk_level],
        ["Duration (months)", st.session_state.months],
        ["Estimated Future Value", f"₹{int(st.session_state.future_value)}"],
    ]

    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4CAF50")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
    ]))

    story.append(Paragraph("📊 Investment Summary", styles["Heading2"]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    if not suggestions.empty:
        header_color = {
            "Low": colors.HexColor("#4CAF50"),
            "Medium": colors.HexColor("#2196F3"),
            "High": colors.HexColor("#F44336")
        }.get(st.session_state.risk_level, colors.HexColor("#2196F3"))

        cols = suggestions.columns.tolist()
        stock_data = [cols]
        for _, row in suggestions.iterrows():
            stock_data.append([str(row[c]) for c in cols])

        stock_table = Table(stock_data, colWidths=[100]*len(cols))
        stock_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), header_color),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
        ]))

        story.append(Paragraph("📈 Suggested Stocks", styles["Heading2"]))
        story.append(stock_table)
        story.append(Spacer(1, 20))

    months = st.session_state.months
    invest = st.session_state.investable_amount
    avg_growth_rate = suggestions["Monthly_Growth"].mean() / 100 if not suggestions.empty else 0.08
    values = [invest * ((1 + avg_growth_rate) ** m) for m in range(months + 1)]

    plt.figure(figsize=(6,3))
    plt.plot(range(months + 1), values, marker="o", color="blue")
    plt.title("Portfolio Growth Over Time")
    plt.xlabel("Months")
    plt.ylabel("Value (₹)")
    plt.grid(True)

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="PNG")
    plt.close()
    img_buffer.seek(0)

    story.append(Paragraph("📉 Projected Portfolio Growth", styles["Heading2"]))
    story.append(Image(img_buffer, width=400, height=200))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Smart Investment Bot", page_icon="💰", layout="wide")
st.title("💬 Smart Investment Simulator & Stock Bot")

with st.expander("Enter Your Financial Details 💵"):
    income = st.number_input("Monthly Income (₹)", min_value=0, step=1000)
    expenses = st.number_input("Monthly Expenses (₹)", min_value=0, step=500)
    savings = st.number_input("Current Savings (₹)", min_value=0, step=500)
    risk_level = st.selectbox("Select Risk Level", ["Low", "Medium", "High"])
    months = st.slider("Investment Duration (months)", 1, 60, 12)

if st.button("💡 Simulate Investments"):
    investable_amount = income - expenses
    suggestions = suggest_stocks(data, investable_amount)

    # Fallback prices from CSV
    fallback_prices = dict(zip(data["Ticker"], data["Price"]))
    tickers = suggestions["Ticker"].tolist()
    prices = fetch_realtime_prices_safe(tickers, fallback_prices)
    suggestions["Real_Time_Price"] = suggestions["Ticker"].map(prices)

    avg_growth_rate = suggestions["Monthly_Growth"].mean() / 100 if not suggestions.empty else 0.08
    future_value = (investable_amount + savings) * ((1 + avg_growth_rate) ** months)

    st.session_state.update({
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "investable_amount": investable_amount,
        "risk_level": risk_level,
        "months": months,
        "future_value": future_value
    })

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Investable Amount", f"₹{investable_amount}")
    col2.metric("📈 Estimated Future Value", f"₹{int(future_value)}")
    col3.metric("⚠️ Risk Level", risk_level)

    st.subheader("📊 Suggested Stocks (with Real-time Prices)")
    st.dataframe(suggestions.style.format({"Price":"₹{:.2f}", "Real_Time_Price":"₹{:.2f}"}))

    st.subheader("📈 Portfolio Growth Simulator")
    sim_months = st.slider("Months to Simulate", 1, 60, 12, key="sim_months")
    sim_values = [investable_amount * ((1 + avg_growth_rate) ** m) for m in range(sim_months + 1)]

    plt.figure(figsize=(10,5))
    plt.plot(range(sim_months + 1), sim_values, marker="o", color="green", label="Portfolio Value")
    plt.fill_between(range(sim_months + 1), sim_values, color="green", alpha=0.1)
    plt.title("Projected Portfolio Growth Over Time")
    plt.xlabel("Months")
    plt.ylabel("Value (₹)")
    plt.grid(True)
    plt.legend()
    st.pyplot(plt)

    pdf_file = create_pdf(suggestions)
    st.download_button(
        "⬇️ Download Full Investment Report (PDF)",
        data=pdf_file,
        file_name="investment_plan.pdf",
        mime="application/pdf",
    )
