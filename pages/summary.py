# can add logo
import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
import streamlit.components.v1 as components
import plotly.express as px
from database.database import get_receipts
st.markdown("""
<style>
@media print {
    div[data-testid="stSidebar"],
    div[data-testid="stCheckbox"],
    div[data-testid="stButton"],
    div[data-testid="stSelectbox"],
    div[data-testid="stDateInput"],
    div[data-testid="stNumberInput"],
    header,
    footer {
        display: none !important;
    }
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    .print-header {
        display: block !important;
        text-align: center;
        border-bottom: 2px solid #333333;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
}

@media screen {
    .print-header {
        display: none;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("Receipt Summary & Reports")
st.write("Analyze your spending habits. Use the filters below to update your report and charts.")
st.caption("💡 To apply filter changes, click **Filter receipts** button")
def extract_data():
    receipts = get_receipts(st.session_state["user_id"])
    st.session_state.all_receipts_full = receipts
    rows = []
    for r in receipts:
        # r = (id, user_id, store, date, total, items, notes, image_path, created_at)
        parsed_date = pd.to_datetime(r[3], errors="coerce")

        if pd.isna(parsed_date):
            continue

        rows.append((parsed_date.date(), r[2], float(r[4] or 0), r[0]))
    return rows

def filter_receipts_by_date(receipts, start, end):
    return [receipt for receipt in receipts if start <= receipt[0] <= end]

def filter_for_month(year, month):
    return [receipt for receipt in st.session_state.all_receipts if int(receipt[0].month)==month and receipt[0].year == year ]


def filter_receipts_by_cost(receipts, min_val, max_val):
    return [receipt for receipt in receipts if min_val <= receipt[2] <= max_val]

def currency(): # just for reference will used based off of pic - assume will only use one currency..
    return "$"

def search_receipts(selected):  # will need to implement properly once receipts have ids
    receipt_id = int(selected.split("ID:")[1])

    for receipt in st.session_state.all_receipts_full:
        if receipt[0] == receipt_id:
            return {
                "id": receipt[0],
                "user_id": receipt[1],
                "store": receipt[2],
                "date": receipt[3],
                "total": receipt[4],
                "items": receipt[5],
                "notes": receipt[6],
                "image_path": receipt[7],
                "created_at": receipt[8]
            }

    return None
    #     for r in st.session_state.all_receipts:
    #     if r[2]==selected[0] and r[4]==selected[1] and r[3]==selected[2]:
    #         print(selected[4])
    #         receipt= r
    # return [receipt for receipt in st.session_state.all_receipts if receipt[0]==selected_id]
    # if receipt:
    #     return { # just for now - will add id in data to use to search for row and send to screen
    #     "store": receipt[2],#name
    #     "date":  receipt[3],#date,
    #     "total": receipt[4],#cost,
    #     "items": receipt[5],
    #     "notes": receipt[6],
    #     "image_path": receipt[7] #(id, user_id, store, date, total, items, notes, image_path, created_at)
    #     }

curr = currency()
# manage default display and rows for filtering 
if "default_display" not in st.session_state:
    st.session_state.default_display = True

if "all_receipts" not in st.session_state:
    st.session_state.all_receipts = extract_data()

if "display_receipts" not in st.session_state:
    st.session_state.display_receipts = st.session_state.all_receipts

# initialize variables  with default values
user_store=None
start_date = None
end_date= None
min_cost = None
max_cost = None

# Filter options
# filter_store_option = st.checkbox("Filter by store")
# if filter_store_option:
  # show all unique store names as well as 'Select store' in dropdown
user_store= st.multiselect("Select a store",  list(set(receipt[1] for receipt in st.session_state.all_receipts)))
print(user_store)
# filter_cost_option = st.checkbox("Filter by cost")
# if filter_cost_option:
cost_filters = st.selectbox("Select cost range", ["All costs", f"Under {curr}50", f"{curr}50-{curr}250", f"{curr}250-{curr}750", f"Over {curr}750", "Custom"])
if cost_filters == f"Under {curr}50":
    min_cost = 0.1
    max_cost = 49
elif cost_filters == f"{curr}50-{curr}250":
    min_cost = 50
    max_cost = 249
elif cost_filters == f"{curr}250-{curr}750":
    min_cost = 250
    max_cost = 749
elif cost_filters == f"Over {curr}750":
    min_cost = 750
    max_cost = 10000 
elif cost_filters == "Custom":
    min_cost = st.number_input("Enter minimum cost", min_value=1, max_value=2000000, step=1, value=80)
    max_cost = st.number_input("Enter maximum cost", min_value=1, max_value=2000000, step=1, value=300)

# filter_date_option = st.checkbox("Filter by date")
# if filter_date_option:
date_filters = st.selectbox("Select date range", ["All dates","Current month", "Last 6 months", "Current year", "Custom range"])
today = date.today()
if date_filters == "Current month":
    start_date = date(today.year, today.month, 1) 
    end_date = today
elif date_filters == "Last 6 months":
    month = today.month - 5
    year = today.year
    if month <= 0:
        month +=12
        year-=1
    start_date = date(year, month, 1) 
    end_date = today
elif date_filters == "Current year":
    start_date = date(today.year, 1, 1)
    end_date = today
elif date_filters == "Custom range":
    start_date = st.date_input("Select starting date")
    end_date = st.date_input("Select ending date")

# Button to implement filtering
# if filter_cost_option or filter_date_option or filter_store_option:
if user_store != [] or date_filters != "All dates" or cost_filters != "All costs":
  btn_filter = st.button(f"Filter receipts")
  if btn_filter:
    st.session_state.default_display = False 
    rows_to_search = st.session_state.all_receipts # search all receipts in database
    # Filter receipts based on user input
    if user_store != []:  
        rows_to_search = [receipt for receipt in rows_to_search if receipt[1] in user_store]
    if date_filters != "All dates":
      rows_to_search = filter_receipts_by_date(rows_to_search, start_date, end_date)
    if cost_filters != "All costs":
      rows_to_search = filter_receipts_by_cost(rows_to_search, min_cost, max_cost)

    st.session_state.display_receipts = rows_to_search # receipts to display to user

    if len(st.session_state.display_receipts) == 0: # if no reciepts fit filtering conditions, check for user input errors
        # if (user_store == "Select store"):
        #     st.error("Please select a store")
        if (start_date and start_date>end_date): # check if invalid date range
            st.error("Start date is after end date - please enter valid date range")
        elif(end_date and end_date>date.today()):
            st.error("Invalid end date - it cannot be set to a future date")
        elif (min_cost and min_cost>max_cost): # check if invalid cost range
            st.error("Invalid costs: minimum cost is larger than maximum cost - please enter valid cost range")
        else:
            # defualt message if no errors were identified
            st.write("Sorry no matching receipts were found - please enter different filtering conditions")

# rendering reciepts in table
if user_store == [] and date_filters == "All dates" and cost_filters == "All costs":
  st.session_state.default_display = True

rows = st.session_state.display_receipts

# if no filtering, show receipts from most recent month
if st.session_state.default_display:
    # rows = filter_for_month(date.today().year, date.today().month) # find receipts from current month
    rows = extract_data()
    if (len(rows)>0): # if there are receipts from current month display relevant message 
        # st.write(f"Receipts from {date.today().strftime("%B")}")
        st.write("All receipts")
    # else: # otherwise find receipts from most recent month and year
    #     if st.session_state.all_receipts:
    #         most_recent_date = st.session_state.all_receipts[0][0]
    #         rows = filter_for_month(most_recent_date.year, most_recent_date.month)
    #         st.write(f"Most recent receipts from {most_recent_date.strftime("%B")} {most_recent_date.year}")
    else: # if there are no receipts then show relevant message
        st.write("No invoices or receipts have been uploaded")
    st.session_state.display_receipts = rows 

# Build dataframe
st.session_state.df = pd.DataFrame([row[:3] for row in st.session_state.display_receipts], columns=["Date", "Store", "Total Cost"])
st.session_state.df.index =  range(1, len(st.session_state.df)+1)
df = st.session_state.df


# show receipts
st.data_editor(st.session_state.df, disabled=True, column_config ={"Total Cost": st.column_config.NumberColumn("Total Cost", format = f"{curr} %.2f")})

# select specific reciept to show details
selected_receipt = st.selectbox("Select a receipt", ["Select receipt"] + list(set(f"{receipt[1]} - {curr}{receipt[2]:.2f} ({receipt[0]})"  for receipt in rows)))

if selected_receipt and selected_receipt != "Select receipt":
    st.session_state.receipt_data = search_receipts(selected_receipt)
    st.switch_page("pages/details.py")

# Load all receipts
receipts = extract_data()  # returns decrypted rows in correct order

# Determine current month
now = datetime.now()
current_year = now.year
current_month = now.month

# Filter receipts to current month
monthly_receipts = []
for r in receipts:
    try:
        receipt_date = datetime.strptime(r[3], "%Y-%m-%d")  # r[3] = date
        if receipt_date.year == current_year and receipt_date.month == current_month:
            monthly_receipts.append(r)
    except Exception:
        pass

# Budget input
budget = st.number_input(
    "Set your monthly budget",
    min_value=0.0,
    value=500.0,
    step=10.0
)

st.session_state.budget = budget

# Calculate monthly spending
total_spent = sum(r[4] for r in monthly_receipts)  # r[4] = total
remaining = st.session_state.budget - total_spent

# Display metrics
st.metric("Total Spent (This Month)", f"${total_spent:.2f}")
st.metric("Remaining Budget", f"${remaining:.2f}")

if remaining < 0:
    st.error("You are over budget.")
else:
    st.success("You are within your budget.")

# pie chart to visualize categories expenses
receipts = extract_data()

# Determine current month
now = datetime.now()
current_year = now.year
current_month = now.month

# Filter receipts to current month
monthly_receipts = []
for r in receipts:
    try:
        receipt_date = datetime.strptime(r[3], "%Y-%m-%d")  # r[3] = date
        if receipt_date.year == current_year and receipt_date.month == current_month:
            monthly_receipts.append(r)
    except Exception:
        pass

# Aggregate totals by category
category_totals = {}

for r in monthly_receipts:
    category = r[8]      # category
    total = r[4]         # total

    category_totals[category] = category_totals.get(category, 0) + total

# Build pie chart
fig = px.pie(
    names=list(category_totals.keys()),
    values=list(category_totals.values()),
    title="Spending by Category (This Month)"
)

st.plotly_chart(fig, use_container_width=True)

# chart to visualize data
if not df.empty:
    st.subheader("📈 Spending Breakdown")

    time = st.selectbox(
        "View timeline by:",
        ["Day", "Week", "Month", "Year"],
        index=0
    )

    df_chart = df.copy()
    df_chart["Date"] = pd.to_datetime(df_chart["Date"])

    if time == "Week":
        df_chart["Timeline"] = df_chart["Date"].dt.to_period("W").dt.start_time
    elif time == "Month":
        df_chart["Timeline"] = df_chart["Date"].dt.to_period("M").dt.start_time
    elif time == "Year":
        df_chart["Timeline"] = df_chart["Date"].dt.to_period("Y").dt.start_time
    else:
        df_chart["Timeline"] = df_chart["Date"]

    # compute chart data
    chart_data = df_chart.groupby("Timeline")["Total Cost"].sum().reset_index()
    total_spent_period = chart_data["Total Cost"].sum()
    total_periods = len(chart_data)

    # Header printout
    st.markdown(f"""
    <div class="print-header">
        <h1>EXPENSE LENS FINANCIAL REPORT</h1>
        <p>Generated on: {date.today().strftime('%Y-%m-%d')} | Granularity: <b>{time}ly</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Render the metrics grid
    rep_col1, rep_col2 = st.columns(2)
    with rep_col1:
        st.metric(f"Total Expenses ({time}ly)", f"${total_spent_period:,.2f}")
    with rep_col2:
        st.metric(f"Active {time}s Logged", total_periods)

    st.markdown("<br>", unsafe_allow_html=True)

    # Render the chart visualization
    st.line_chart(data=chart_data, x="Timeline", y="Total Cost")

    st.divider()

    # Printable report trigger button
    st.subheader("Export Report")
    if st.button("Open System Print Dialogue"):
        components.html("""
        <script>
            window.parent.print();
        </script>
        """, height=0)

# Navigation Back Home
if st.button("← Back to Upload Screen"):
    st.switch_page("app.py")
