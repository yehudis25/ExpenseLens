hide_streamlit_style = """
    <style>
        /* Hide the hamburger menu */
        #MainMenu {visibility: hidden;}

        /* Hide the footer */
        footer {visibility: hidden;}

        /* Hide the sidebar */
        section[data-testid="stSidebar"] {display: none !important;}
    </style>
"""
import streamlit as st
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
from datetime import datetime
from database.database import get_receipts, get_user_budget, update_user_budget
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Budget Overview", page_icon="💰")

st.title("💰 Budget Management")

user_id = st.session_state.get("user_id")  # however you store logged-in user

# Load user-specific budget
budget = get_user_budget(user_id)

# Budget input
new_budget = st.number_input(
    "Set your monthly budget ($)",
    min_value=0.0,
    step=10.0,
    value=budget
)

# Save if changed
if new_budget != budget:
    update_user_budget(user_id, new_budget)
    budget = new_budget


receipts = get_receipts(user_id)
current_month_str = datetime.now().strftime("%Y-%m")
monthly_receipts = []
total_spent = 0.0

now = datetime.now()
current_year = now.year
current_month = now.month

def normalize_date(date_str):
    if not date_str or "Unknown" in date_str:
        return None
    parsed = pd.to_datetime(date_str, dayfirst=True, errors="coerce")
    if pd.isnull(parsed):
        parsed = pd.to_datetime(date_str, errors="coerce")
    return parsed
for r in receipts:
    parsed_date = normalize_date(r[3])
    if pd.notnull(parsed_date) and parsed_date.year == current_year and parsed_date.month == current_month:
        monthly_receipts.append(r)
        total_spent += r[4]

remaining_budget = budget - total_spent

#  Display the budget health metrics
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Budget Limit", f"${budget:,.2f}")
col2.metric("Total Spent to Date", f"${total_spent:,.2f}")

# Color the remaining metric based on whether you are over or under budget
if remaining_budget >= 0:
    col3.metric("Remaining Balance", f"${remaining_budget:,.2f}", delta=f"${remaining_budget:,.2f}")
else:
    col3.metric("Remaining Balance", f"${remaining_budget:,.2f}", delta=f"${remaining_budget:,.2f}", delta_color="inverse")

# visual progress bar
if budget > 0:
    progress_percentage = min(total_spent / budget, 1.0)
    st.progress(progress_percentage)
    st.write(f"You have used **{progress_percentage * 100:.1f}%** of your monthly budget.")

# pie chart to visualize categories expenses
# Aggregate totals by category
category_totals = {}
for r in monthly_receipts:
    category = str(r[8]).strip() or "Uncategorized"  # ensure non-empty
    total = float(r[4])
    category_totals[category] = category_totals.get(category, 0) + total

# Convert to DataFrame for Plotly
df = pd.DataFrame({
    "Category": list(category_totals.keys()),
    "Total": list(category_totals.values())
})
# st.write("Categories from DB:", [r[8] for r in monthly_receipts])
# st
# Build pie chart colored by category
fig = px.pie(
    df,
    names="Category",
    values="Total",
    color="Category",
    title="Spending by Category (This Month)",
)
# st.write(df)
# for r in monthly_receipts:
#     st.write(f"Store: {r[2]}, Category: {r[8]}, Date: {r[3]}")
#     st.write("Category index 8:", r[8], " | created_at index 9:", r[9])
# st.write([r[8] for r in get_receipts()])

st.plotly_chart(fig, use_container_width=True)

if st.button("View Receipts"):
    st.switch_page("pages/summary.py")

if st.button("← Back to Upload Screen"):
    st.switch_page("pages/upload_receipt.py")

