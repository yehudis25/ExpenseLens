# can add logo
import streamlit as st
import pandas as pd
from datetime import date
from database.database import get_receipts, filter_receipts
import streamlit.components.v1 as components
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

# Define your data function locally so the page can access it
# def extract_data():
#     return [
#         (date(2026, 6, 10), "Pick 'n Pay", 1000.00),
#         (date(2026, 6, 12), "Clicks", 550.50),
#         (date(2026, 6, 22), "Corner Cafe", 250.80),
#         (date(2026, 10, 4), "Corner Cafe", 250.80)
#     ]

# def filter_receipts_by_date(receipts, start, end):
#     return [receipt for receipt in receipts if start <= receipt[0] <= end]

# def filter_receipts_by_cost(receipts, min_val, max_val):
#     return [receipt for receipt in receipts if min_val <= receipt[2] <= max_val]

def currency(): # just for reference will used based off of pic - assume will only use one currency..
    return "$"

def search_receipts(selected):  # will need to implement properly once receipts have ids
    name = selected.split("-")[0].strip()
    cost = selected.split("-")[1].split("(")[0].strip()[1:]
    date = selected.split("(")[1][0:-1]
    return { # just for now - will add id in data to use to search for row and send to screen
      "store": name,
      "date": date,
      "total": cost,
      "items": "",
      "notes": ""
    }
# Always initialize 'rows' with default data right away
curr = currency()
rows = filter_receipts()
default_display = True
user_store = "Select store"
start_date = None
end_date= None
min_cost = None
max_cost = None
# Filter options
filter_store_option = st.checkbox("Filter by store")
if filter_store_option:
  # show store names as well as 'Select store' in dropdown
  user_store= st.selectbox("Select a store", ["Select store"] + list(set(receipt[1] for receipt in filter_receipts())))
  if user_store and user_store != "Select store":
      default_display = False
      # show receipts with matching store that user selected
    #   rows = [receipt for receipt in get_receipts() if receipt[1] == user_store]

filter_cost_option = st.checkbox("Filter by cost")
if filter_cost_option:
  min_cost = st.number_input("Enter minimum cost", min_value=1, max_value=2000000, step=1, value=100)
  max_cost = st.number_input("Enter maximum cost", min_value=1, max_value=2000000, step=1, value=500)
#   default_display = False
else: 
    min_cost = None
    max_cost = None

filter_date_option = st.checkbox("Filter by date")

if filter_date_option:
  start_date = st.date_input("Select starting date")
  end_date = st.date_input("Select ending date")
else:
    start_date=None
    end_date=None
#   default_display = False

# button to implement cost and date filtering
if filter_cost_option or filter_date_option or filter_store_option and user_store != "Select store":
    # if filter_store_option:
    #     btn_message = "store"
    # if filter_cost_option:
    #     btn_message = "cost"
    # if filter_date_option:
    #     btn_message += " and date"
  btn_filter = st.button(f"Filter receipts")
  # Filtering receipts based on user input
  if btn_filter:
    default_display = False
    st.write(user_store)
    st.write(min_cost)
    st.write(max_cost)
    st.write(start_date)
    st.write(end_date)
    results = filter_receipts(user_store, min_cost, max_cost, start_date, end_date)



    ############################
    # if filter_store_option: # use receipts that have already been filtered by store
    #     rows_to_search = rows
    # else:
    #   rows_to_search = extract_data() # use all receipts
    # if filter_date_option:
    #   rows_to_search = filter_receipts_by_date(rows_to_search, start_date, end_date)
    # if filter_cost_option:
    #   rows_to_search = filter_receipts_by_cost(rows_to_search, min_cost, max_cost)
    # st.session_state.rows = rows_to_search
    # rows = st.session_state.rows
    ##################################

    st.session_state.rows = results
    rows = st.session_state.rows

    if len(rows) == 0:
      st.write("Sorry no matching receipts were found - please enter different filtering conditions")

# rendering reciepts in table
if not filter_store_option and not filter_date_option and not filter_cost_option:
  default_display = True

# build dataframe
st.session_state.df = pd.DataFrame(rows, columns=["Date", "Store", "Total Cost"])
st.session_state.df.index =  range(1, len(st.session_state.df)+1)
df = st.session_state.df

# if no filters are applied show message that receipts from current month are displayed
if default_display:
  st.write(f"Receipts from {date.today().strftime('%B')}")
  default_display = True

# show receipts
st.data_editor(st.session_state.df, disabled=True, column_config ={"Total Cost": st.column_config.NumberColumn("Total Cost", format = f"{curr} %.2f")})

# select specific reciept to show details
selected_receipt = st.selectbox("Select a receipt", ["Select receipt"] + list(set(f"{receipt[1]} - {curr}{receipt[2]:.2f} ({receipt[0]})"  for receipt in rows)))
if selected_receipt and selected_receipt != "Select receipt":
    st.session_state.receipt_data = search_receipts(selected_receipt)
    st.switch_page("pages/details.py")

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
