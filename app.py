import streamlit as st
import pandas as pd
import os
import sys

sys.path.append("/content/expense_lens")

from database.database import (
    create_tables,
    save_receipt,
    save_image,
    save_feedback
)

from utils.receipt_processor import process_receipt

# configure the page, must run first
st.set_page_config(
    page_title="ExpenseLens",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Create database tables
create_tables()

LOGO_PATH = "/content/drive/MyDrive/ExpenseLensDatasets/logo.png"
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


if uploaded_file:
    st.success("Receipt uploaded successfully!")
    st.image(uploaded_file, width=300)

    st.session_state["uploaded_image"] = uploaded_file
    # OCR + AI extraction

    if "receipt_data" not in st.session_state:


        try:

            extracted = process_receipt(uploaded_file)

            st.session_state["receipt_data"] = extracted


        except Exception as e:

            st.error(
                "Receipt processing failed."
            )

            st.write(e)



    data = st.session_state["receipt_data"]

    st.divider()
    st.subheader("✏️ Review & Edit AI Extraction")

    with st.form("receipt_form"):

        store = st.text_input(
            "Store",
            st.session_state["receipt_data"]["store"]
        )

        date = st.text_input(
            "Date",
            st.session_state["receipt_data"]["date"]
        )

        total = st.number_input(
            "Total",
            min_value=0.0,
            value=float(st.session_state["receipt_data"]["total"]),
            step=0.01
        )

        items = st.text_area(
            "Items",
            st.session_state["receipt_data"]["items"]
        )

        notes = st.text_area(
            "Notes",
            st.session_state["receipt_data"]["notes"]
        )

        saved = st.form_submit_button("💾 Save Receipt")


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

                # Save receipt image into Google Drive
                image_path = save_image(uploaded_file)


                # Save receipt information into SQLite
                result = save_receipt(
                    receipt,
                    image_path
                )


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
