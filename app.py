# module for startup page - where user uploades and edits receipts
import streamlit as st
import pandas as pd
import os
from PIL import Image, UnidentifiedImageError
import io
from utils.receipt_processor import process_receipt, receipt_check, extract_raw_text
from database.database import (
    create_tables,
    save_receipt,
    save_image,
    save_feedback
)
create_tables()
# create different user (database) for each user - to be continued...
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "user1"


# configure the page, must run first
st.set_page_config(
    page_title="ExpenseLens",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)



# logo
LOGO_PATH = "/workspaces/ExpenseLens/assets/Logo.png"

col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
    else:
        st.markdown("# 🔍")
with col2:
    st.title("ExpenseLens")
    st.caption("Precision Expense Tracking & Receipt Analysis")
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


# user can upload a file
uploaded_file = st.file_uploader(
    "Upload a receipt image",
    type=["png", "jpg", "jpeg"],
    help="Upload a clear image of a receipt for automatic information extraction."
)

# sample receipts to test with
import os

sample_files = []

for root, dirs, files in os.walk("data"):
    for file in files:
        sample_files.append(os.path.join(root, file))


sample = st.selectbox(
    "Or test with sample files",
    ["None"] + sample_files
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
    
    try:
        st.image(image_input, width=300)
    except UnidentifiedImageError:
        st.error("Invalid image - please upload another image")
    else: # only runs if no exception thrown
       # OCR + VALIDATION
        if "receipt_data" not in st.session_state:

            with st.spinner("Analyzing document..."):
                extracted_text = extract_raw_text(image_input)

                # Run LLM validator
                if not receipt_check(extracted_text):
                    st.error("This does not appear to be a receipt or invoice.")
                    st.stop()

                st.session_state["receipt_data"] = process_receipt(image_input)
            st.success("Valid receipt detected! Extracting structured data...")
        data = st.session_state["receipt_data"]

        st.divider()
        st.subheader("✏️ Review & Edit AI Extraction")
        # show AI extracted data
        with st.form("receipt_form"):

            store = st.text_input(
                "Store",
                st.session_state["receipt_data"].get("store", "")
            )

            date = st.text_input(
                "Date",
                st.session_state["receipt_data"].get("date", "")
            )

            total = st.number_input(
                "Total",
                min_value=0.0,
                value=float(st.session_state["receipt_data"].get("total", 0)),
                step=0.01
            )

            st.markdown("### Items")
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

                df = pd.DataFrame(items_list)
                df = df.drop(columns=["id", "pk", "item_id"], errors="ignore")  # hide primary keys

                if {"price", "quantity"}.issubset(df.columns):
                    # Ensure price and quantity are treated as numbers (invalid values turn into NaN)
                    df["price"] = pd.to_numeric(df["price"], errors="coerce")
                    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
                    
                    df["subtotal"] = df["price"] * df["quantity"]

                edited_df = st.data_editor(df, use_container_width=True)
                items = edited_df.to_dict(orient="records")

            except Exception as e:
                st.warning("Could not display items as a table.")
                st.write(e)

            notes = st.text_area(
                "Notes",
                st.session_state["receipt_data"].get("notes", "")
            )

            saved = st.form_submit_button("💾 Save Receipt")

            # save data from receipt
            if saved:
                receipt = {

                    "store": store,
                    "date": date,
                    "total": total,
                    "items": items,
                    "notes": notes
                }
                st.session_state["receipt_data"] = receipt



                try:
                    # Save receipt image 
                    image_path = save_image(image_input, st.session_state["user_id"])

                    # Save receipt information into SQLite
                    result = save_receipt(
                    receipt,
                    image_path,
                    st.session_state["user_id"]
                )
                    # did it save properly?
                    if result:
                        st.success(
                            "Receipt saved permanently!"
                        )

                    else:
                        st.error(
                            "Could not save receipt."
                        )
                except Exception as e:
                    st.error(
                        "Database save failed"
                    )


# add page here
if st.button("View Receipts"):
    st.switch_page("pages/summary.py")


# rate activities here
st.divider()
st.subheader("Feedback")

with st.form("feedback_form"):
    rating = st.slider(
        "Rate your experience",
        min_value=1,
        max_value=5,
        value=3
    )
    comment = st.text_area(
        "Leave a comment here:"
    )

    submitted = st.form_submit_button("Submit Feedback")

if submitted:
    # save feedback to dtbs
    try:
        save_feedback(
            rating,
            comment
        )


        st.success(
            "Thank you for your feedback!"
        )

        st.write(
            "Your rating:",
            "⭐" * rating
        )


    except Exception as e:
        st.error(
            "Could not save feedback"
        )

        st.write(e)
