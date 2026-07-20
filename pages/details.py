# page with details of receipt
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
import os
from io import BytesIO
from PIL import Image
from utils.encryption import decrypt_bytes
if "user_id" not in st.session_state:
    st.warning("Please login first")
    st.switch_page("app.py")
receipt_data = st.session_state.get("receipt_data")

if receipt_data is None:
    st.warning("No receipt loaded")
    st.stop()

st.title("🧾Receipt Detail")

col1, col2 = st.columns(2)

with col1:

    st.subheader("Receipt Image")

    image_path = receipt_data.get("image_path")

    if image_path and not os.path.isabs(image_path):
        image_path = os.path.join("/workspaces/ExpenseLens", image_path)

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encrypted_bytes = f.read()

        try:
            image_bytes = decrypt_bytes(encrypted_bytes)
        except:
            # old images saved before encryption
            image_bytes = encrypted_bytes
        image = Image.open(BytesIO(image_bytes))

        st.image(image, use_container_width=True)
    else:
        st.error(f"Image not found: {image_path}")

with col2:
    st.subheader("Receipt Information")

    st.subheader("Store")
    st.write(receipt_data.get("store", ""))

    st.subheader("Date")
    st.write(receipt_data.get("date", ""))

    st.subheader("Total ($)")
    st.write(f"${float(receipt_data.get('total') or 0):.2f}")

    st.subheader("Items")

    items = receipt_data.get("items", [])

    if isinstance(items, list):
        st.dataframe(items)
    else:
        st.write(items)

    st.subheader("Notes")
    st.write(receipt_data.get("notes", ""))

# Navigation Back Home
if st.button("← Back to Upload Screen"):
    st.switch_page("pages/upload_receipt.py")
if st.button("View Receipts"):
    st.switch_page("pages/summary.py")
