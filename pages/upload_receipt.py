# module for startup page - where user uploades and edits receipts
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
import pandas as pd
import os
from datetime import datetime 
from PIL import UnidentifiedImageError
from utils.receipt_processor import process_receipt, receipt_check, extract_raw_text
from database.database import (
    save_receipt,
    save_image
)

# make sure user is logged in
if "user_id" not in st.session_state:
    st.warning("Please login first")
    st.switch_page("app.py")

st.markdown("""
### Welcome to ExpenseLens

ExpenseLens helps you organize and manage your expenses by extracting information from receipt images.
Upload a receipt, review the extracted information, make any necessary edits, and save it for future reference.
""")

# instructions and descriptions
with st.expander("How It Works"):
    st.write("""
    1. Upload a receipt image.
    2. ExpenseLens extracts receipt information.
    3. Review and edit extracted data.
    4. Save the receipt to your expense database.
    """)

# Privacy disclaimer before upload
st.markdown("""
<style>
.privacy-box {
    background-color: #172A45;
    border: 1px solid #FF3B30;
    padding: 18px;
    border-radius: 12px;
    color: #FFFFFF;
    font-size: 14px;
}
.privacy-title {
    color: #FF3B30;
    font-size: 18px;
    font-weight: bold;
}
</style>

<div class="privacy-box">
    <div class="privacy-title">🔒 Receipt Privacy Notice</div>
    <br>
    Your receipt images may contain sensitive information such as store details,
    purchase history, or payment information. Only upload receipts you are comfortable
    sharing with this application.
    <br><br>
    ExpenseLens uses uploaded receipts only for expense analysis and organization.
    Please avoid uploading receipts containing unnecessary personal information.
</div>
""", unsafe_allow_html=True)


st.subheader("Add a Receipt")

# Initialize the save tracking state if it doesn't exist
if "receipt_saved" not in st.session_state:
    st.session_state.receipt_saved = False
input_method = st.radio(
    "Choose how to add a receipt:",
    ["Upload Image", "Take Picture"]
)
# reset saved status when new file is saved
def reset_save_state():
    st.session_state.receipt_saved = False

uploaded_file = None

if input_method == "Upload Image":
    uploaded_file = st.file_uploader(
        "Upload a receipt image",
        type=["png", "jpg", "jpeg"],
        help="Upload a clear image of a receipt.",
        on_change=reset_save_state  # Resets state when a new file is uploaded
    )

else:
    uploaded_file = st.camera_input("Take a picture of your receipt")

# sample receipts to test with

sample_files = []

for root, dirs, files in os.walk("data"):
    for file in files:
        sample_files.append(os.path.join(root, file))


sample = st.selectbox(
    "Or test with sample files",
    ["None"] + sample_files,
    on_change=reset_save_state
)

if sample != "None":
    uploaded_file = sample

image_input = None

image_input = uploaded_file

if isinstance(sample, str) and sample != "None":
    image_input = sample
if image_input:
    # detect new receipt
    current_file = str(image_input)

    if st.session_state.get("last_uploaded") != current_file:
        st.session_state.pop("receipt_data", None)
        st.session_state["last_uploaded"] = current_file
        st.session_state["receipt_saved"] = False
    
    try:
        st.image(image_input, width=300)
    except UnidentifiedImageError:
        st.error("Invalid image - please upload another image")
    else: # only runs if no exception thrown
       # OCR + VALIDATION
        if "receipt_data" not in st.session_state:

            # First extract text
            with st.spinner("Uploading receipt..."):
                print("STEP 1")
                extracted_text = extract_raw_text(image_input)
                print("STEP 2")
            if not receipt_check(extracted_text):
                st.error("This does not appear to be a receipt.")
                st.stop()

            # Now run LLM extraction
            with st.spinner("Processing receipt..."):
                st.session_state["receipt_data"] = process_receipt(extracted_text)

                st.success("Valid receipt detected!")

            data = st.session_state["receipt_data"]

        st.divider()
        st.subheader("✏️ Review & Edit AI Extraction")
        # show AI extracted data
        with st.form("receipt_form"):

            store = st.text_input(
                "Store",
                st.session_state["receipt_data"].get("store", "")
            )

            str_date = st.session_state["receipt_data"].get("date", "")
            default_date = None
            # loop through valid date formats
            for formats in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"):
                try:
                    default_date = datetime.strptime(str_date, formats).date()
                    break
                except (ValueError, TypeError):
                    pass

            if default_date:
                date = st.date_input("Date", value=default_date)
            else:
                date = st.text_input("Date", value=str_date)

            total = st.number_input(
                "Total",
                min_value=0.0,
                value=float(st.session_state["receipt_data"].get("total", 0)),
                step=0.01
            )

            st.markdown("### Items")
            items = []
            try:
            # Convert extracted items into a DataFrame
                items_list = st.session_state["receipt_data"].get("items", [])
                if isinstance(items_list, str):
                    # If LLM returned a string, try to parse it
                    import ast
                    try:
                        items_list = ast.literal_eval(items_list)
                    except (ValueError, SyntaxError):
                        st.warning("AI could not format items correctly.")
                        items_list = []
                # Create DataFrame
                df = pd.DataFrame(items_list)
                df = df.drop(columns=["id", "pk", "item_id"], errors="ignore")  # hide primary keys
                # Make sure required columns always exist
                required_columns = ["name", "quantity", "price"]

                for col in required_columns:
                    if col not in df.columns:
                        if col == "quantity":
                            df[col] = 1
                        elif col == "price":
                            df[col] = 0.0
                        else:
                            df[col] = ""

                # Keep columns in order
                df = df[required_columns]

                # Convert numeric columns
                df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
                df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1)

                # Calculate subtotal
                df["subtotal"] = df["price"] * df["quantity"]

                # Editable table with Add/Delete Row support
                edited_df = st.data_editor(
                    df,
                    width="stretch",
                    hide_index=True,
                    num_rows="dynamic"
                )

                # Recalculate subtotal after user edits
                edited_df["price"] = pd.to_numeric(
                    edited_df["price"], errors="coerce"
                ).fillna(0.0)

                edited_df["quantity"] = pd.to_numeric(
                    edited_df["quantity"], errors="coerce"
                ).fillna(1)

                edited_df["subtotal"] = (
                    edited_df["price"] * edited_df["quantity"]
                )

                items = edited_df.to_dict(orient="records")

            except Exception as e:
                st.warning("Could not display items as a table.")
                st.write(e)

            notes = st.text_area(
                "Notes",
                st.session_state["receipt_data"].get("notes", "")
            )
            CATEGORIES = [
                "",
                "Advertising",
                "Travel Expenses",
                "Commissions",
                "Contract Labor",
                "Insurance",
                "Legal Services",
                "Office Expenses",
                "Meals",
                "Utilities",
                "Other"
            ]

            category = st.selectbox(
                "Category",
                CATEGORIES,
                format_func=lambda x: "Select a category..." if x == "" else x
            )

            # saved = st.form_submit_button("💾 Save Receipt")
            saved = st.form_submit_button(
                "💾 Save Receipt",
                disabled=st.session_state.receipt_saved
            )

            # save data from receipt
            if saved:
                if st.session_state.receipt_saved:
                    st.warning("This receipt has already been saved.")
                    st.stop()
                if not store or not date:
                    st.error("Receipt information is missing. Please fill in store and date before saving.")
                    st.stop()
                image_path = save_image(image_input, st.session_state["user_id"])
            
                if hasattr(date, "isoformat"):
                    date_value = date.isoformat() # check if date object and convert to string
                else: # date is string
                    date_value = date

                receipt = {
                    "store": store,
                    "date": date_value,
                    "total": total,
                    "items": items,
                    "notes": notes,
                    "image_path": image_path,
                    "category": category
                }
                st.session_state["receipt_data"] = receipt

                try:

                    receipt_id = save_receipt(
                        data=receipt,
                        image_path=image_path,
                        user_id=st.session_state["user_id"]
                    )

                    st.session_state["receipt_data"]["id"] = receipt_id
                
                    # did it save properly?
                    if receipt_id:
                        st.session_state.receipt_saved = True
                        st.success("Receipt saved permanently!")
                        print("SAVED")
                    else:
                        st.error(
                            "Could not save receipt."
                        )
                        print("ERROR")
                except Exception as e:
                    st.error(
                        "Database save failed"
                    )
                    st.write(e)

# add page here
if st.button("View Receipts"):
    st.switch_page("pages/summary.py")
if st.button("View Budget Overview"):
    st.switch_page("pages/budget.py")

