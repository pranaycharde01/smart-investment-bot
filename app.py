import streamlit as st
import pandas as pd

# Set up Streamlit page
st.set_page_config(page_title="Smart Investment Bot", page_icon="💰")
st.title("💬 Smart Investment Suggestion Bot")

# Load stock data
@st.cache_data
def load_stock_data():
    return pd.read_csv("stock_data.csv")

# Suggest best low-cost high-growth stocks
def suggest_stocks(data, investable_amount):
    affordable = data[data["Price"] <= investable_amount]
    top_stocks = affordable.sort_values(by="Monthly_Growth", ascending=False)
    return top_stocks.head(3)

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1

# Step 1: Input income
if st.session_state.step == 1:
    st.chat_message("assistant").write("Hi! What's your monthly income?")
    income = st.number_input("Monthly Income (₹)", min_value=1, step=1000)

    if income <= 0:
        st.warning("Please enter your monthly income to continue.")

    if income > 0 and st.button("Next"):
        st.session_state.income = income
        st.session_state.step = 2
        st.rerun()

# Step 2: Input expenses
elif st.session_state.step == 2:
    st.chat_message("assistant").write("And what are your total monthly expenses?")
    expenses = st.number_input("Monthly Expenses (₹)", min_value=0, step=1000)

    if expenses < 0:
        st.warning("Expenses cannot be negative.")

    if expenses >= 0 and st.button("Next"):
        st.session_state.expenses = expenses
        st.session_state.step = 3
        st.rerun()

# Step 3: Calculate savings and investable amount
elif st.session_state.step == 3:
    income = st.session_state.income
    expenses = st.session_state.expenses
    savings = income - expenses

    if savings <= 0:
        st.chat_message("assistant").error(
            "Oops! Your expenses exceed or equal your income. No savings to invest."
        )
        if st.button("🔁 Re-enter Income & Expenses"):
            st.session_state.step = 1
            st.rerun()
    else:
        invest_min = savings * 0.05
        invest_max = savings * 0.10

        st.chat_message("assistant").success(f"Great! You are saving ₹{savings}/month.")
        st.chat_message("assistant").info(
            f"You can invest between ₹{int(invest_min)} and ₹{int(invest_max)} per month."
        )

        st.session_state.savings = savings
        st.session_state.investable_amount = invest_max
        if st.button("🔍 Analyze Stocks"):
            st.session_state.step = 4
            st.rerun()

# Step 4: Analyze and suggest stocks
elif st.session_state.step == 4:
    st.chat_message("assistant").write("📈 Analyzing current stock trends...")
    data = load_stock_data()
    investable_amount = st.session_state.investable_amount
    suggestions = suggest_stocks(data, investable_amount)

    if suggestions.empty:
        st.chat_message("assistant").warning(
            "No stocks found under your investable amount. Try saving more!"
        )
    else:
        st.chat_message("assistant").success("📊 Suggested Stocks:")
        for _, row in suggestions.iterrows():
            st.chat_message("assistant").markdown(
                f"- **{row['Company']}** ({row['Ticker']}) — ₹{row['Price']} | 📈 {row['Monthly_Growth']}% growth"
            )

    if st.button("🔁 Start Over"):
        st.session_state.clear()
        st.rerun()
