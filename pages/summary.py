# can add logo
import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
from database.database import get_receipts

if "user_id" not in st.session_state:
    st.warning("Please login first")
    st.switch_page("app.py")
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

def extract_data():
    receipts = get_receipts(st.session_state["user_id"])
    st.session_state.all_receipts_full = receipts

    rows = []

    for r in receipts:
        # r = (id, user_id, store, date, total, items, notes, image_path, created_at)
        try:
            rows.append((pd.to_datetime(r[3]).date(), r[2], float(r[4]), r[0]))
        except:
            continue
    return rows

def filter_receipts_by_date(receipts, start, end):
    return [receipt for receipt in receipts if start <= receipt[0] <= end]

def filter_for_month(cur_year, cur_month):
    return [receipt for receipt in st.session_state.all_receipts if int(receipt[0].month)==cur_month and receipt[0].year == cur_year ]


def filter_receipts_by_cost(receipts, min_val, max_val):
    return [receipt for receipt in receipts if min_val <= receipt[2] <= max_val]

def currency(): # just for reference will used based off of pic - assume will only use one currency..
    return "$"

def search_receipts(selected):
    for receipt in st.session_state.all_receipts_full:

        display_name = f"{receipt[2]} - ${receipt[4]:.2f} ({receipt[3]})"

        if display_name == selected:
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

curr = currency()
# manage default display and rows for filtering 
if "default_display" not in st.session_state:
    st.session_state.default_display = True

if "all_receipts" not in st.session_state:
    st.session_state.all_receipts = extract_data()

if "all_receipts_full" not in st.session_state:
    st.session_state.all_receipts_full = get_receipts(
        st.session_state["user_id"]
    )

if "display_receipts" not in st.session_state:
    st.session_state.display_receipts = st.session_state.all_receipts

# initialize variables  with default values
user_store=None
start_date = None
end_date= None
min_cost = None
max_cost = None

# Filter options
filter_store_option = st.checkbox("Filter by store")
if filter_store_option:
  # show all unique store names as well as 'Select store' in dropdown
  user_store= st.selectbox("Select a store", ["Select store"] + list(set(receipt[1] for receipt in st.session_state.all_receipts)))

filter_cost_option = st.checkbox("Filter by cost")
if filter_cost_option:
  min_cost = st.number_input("Enter minimum cost", min_value=1, max_value=2000000, step=1, value=80)
  max_cost = st.number_input("Enter maximum cost", min_value=1, max_value=2000000, step=1, value=300)

filter_date_option = st.checkbox("Filter by date")
if filter_date_option:
  start_date = st.date_input("Select starting date")
  end_date = st.date_input("Select ending date")


# Button to implement filtering
if filter_cost_option or filter_date_option or filter_store_option:
  btn_filter = st.button(f"Filter receipts")
  if btn_filter:
    st.session_state.default_display = False 
    rows_to_search = st.session_state.all_receipts # search all receipts in database
    # Filter receipts based on user input
    if filter_store_option:
        rows_to_search = [receipt for receipt in rows_to_search if receipt[1] == user_store]
    if filter_date_option:
      rows_to_search = filter_receipts_by_date(rows_to_search, start_date, end_date)
    if filter_cost_option:
      rows_to_search = filter_receipts_by_cost(rows_to_search, min_cost, max_cost)

    st.session_state.display_receipts = rows_to_search # receipts to display to user

    if len(st.session_state.display_receipts) == 0: # if no reciepts fit filtering conditions, check for user input errors
        if (user_store == "Select store"):
            st.error("Please select a store")
        elif (start_date and start_date>end_date): # check if invalid date range
            st.error("Start date is after end date - please enter valid date range")
        elif(end_date and end_date>date.today()):
            st.error("Invalid end date - it cannot be set to a future date")
        elif (min_cost and min_cost>max_cost): # check if invalid cost range
            st.error("Invalid costs: minimum cost is larger than maximum cost - please enter valid cost range")
        else:
            # defualt message if no errors were identified
            st.write("Sorry no matching receipts were found - please enter different filtering conditions")

# rendering reciepts in table
if not filter_store_option and not filter_date_option and not filter_cost_option:
  st.session_state.default_display = True

rows = st.session_state.display_receipts

# if no filtering, show receipts from most recent month
if st.session_state.default_display:
    rows = filter_for_month(date.today().year, date.today().month) # find receipts from current month
    if (len(rows)>0): # if there are receipts from current month display relevant message 
        st.write(f"Receipts from {date.today().strftime("%B")}")
    else: # otherwise find receipts from most recent month and year
        if st.session_state.all_receipts:
            most_recent_date = st.session_state.all_receipts[0][0]
            rows = filter_for_month(most_recent_date.year, most_recent_date.month)
            st.write(f"Most recent receipts from {most_recent_date.strftime("%B")} {most_recent_date.year}")
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
selected_receipt = st.selectbox(
    "Select a receipt",
    ["Select receipt"] + [
        f"{receipt[1]} - ${receipt[2]:.2f} ({receipt[0]})"
        for receipt in rows
    ]
)

if selected_receipt and selected_receipt != "Select receipt":
    st.session_state.receipt_data = search_receipts(selected_receipt)
    st.switch_page("pages/details.py")

# budget!
receipts = st.session_state.all_receipts  # lists of reciepts so budget can access it
budget = st.number_input(
    "Set your monthly budget",
    min_value=0.0,
    value=500.0,
    step=10.0
)

if "budget" not in st.session_state:
    st.session_state.budget = budget
else:
    st.session_state.budget = budget

total_spent = sum(r[2] for r in receipts)
remaining = st.session_state.budget - total_spent

st.metric("Total Spent", f"${total_spent:.2f}")
st.metric("Remaining Budget", f"${remaining:.2f}")

if remaining < 0:
    st.error("You are over budget.")
else:
    st.success("You are within your budget.")

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
