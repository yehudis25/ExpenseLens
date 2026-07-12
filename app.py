# module for startup page - where user uploades and edits receipts
# auto start ollama server
import subprocess
import psutil
import time

def ensure_ollama_running():
    # Check if Ollama is already running
    for p in psutil.process_iter(attrs=["name"]):
        if "ollama" in p.info["name"].lower():
            return  # already running

    # Start Ollama server
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # give it a moment to boot
    except Exception as e:
        print("Could not start Ollama:", e)

ensure_ollama_running()

import streamlit as st
from database.database import create_tables, DB_PATH
import os
<<<<<<< HEAD
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

=======
import hashlib
import sqlite3
>>>>>>> 20b5d5682c44055b720a52b0e41c4363810e272d

# configure the page, must run first
st.set_page_config(
    page_title="ExpenseLens",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)


create_tables()


# funtion which turns the password into hashes
def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# function to check if user exists
def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id 
        FROM users
        WHERE username=? AND password=?
        """,
        (
            username,
            hash_password(password)
        )
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

# function to create new account
def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users(username, password)
            VALUES (?,?)
            """,
            (
                username,
                hash_password(password)
            )
        )

        conn.commit()
        return True

    # no duplicate users
    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()

# logo
LOGO_PATH = "/workspaces/ExpenseLens/assets/Logo.png"

<<<<<<< HEAD
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=350)
else:
    st.markdown("# 🔍")

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

            # First extract text
            with st.spinner("Analyzing document..."):
                extracted_text = extract_raw_text(image_input)

            # Run LLM validator OUTSIDE spinner
            if not receipt_check(extracted_text):
                st.error("This does not appear to be a receipt or invoice.")
                st.stop()

            # Now run LLM extraction
            with st.spinner("Extracting structured data..."):
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
                image_path = save_image(image_input, st.session_state["user_id"])
                receipt = {

                    "store": store,
                    "date": date,
                    "total": total,
                    "items": items,
                    "notes": notes,
                    "image_path": image_path
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
=======
col1, col2 = st.columns([3, 4])  # wider column for the logo

with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=350)
    else:
        st.markdown("# 🔍")

with col2:
    st.title("ExpenseLens")
    st.caption("Precision Expense Tracking & Receipt Analysis")
>>>>>>> 20b5d5682c44055b720a52b0e41c4363810e272d
st.divider()

#login

# checks if already logged in
if "user_id" not in st.session_state:

    st.subheader("🔐 Login")

    option = st.radio(
        "Choose an option",
        ["Login", "Create Account"]
    )

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    # create a new account
    if option == "Create Account":

        if st.button("Create Account"):

            if create_user(username, password):
                st.success(
                    "Account created! Please login."
                )
            else:
                st.error(
                    "Username already exists."
                )
    # try logging in
    else:
        if st.button("Login"):
            user_id = login(
                username,
                password
            )
            if user_id:

                st.session_state["user_id"] = user_id
                st.success(
                    "Login successful!"
                )
                st.switch_page(
                    "pages/upload_receipt.py"
                )
            else:
                st.error(
                    "Invalid username or password"
                )
else:
    st.success(
        "You are logged in!"
    )

    if st.button("Upload Receipt"):
        st.switch_page(
            "pages/upload_receipt.py"
        )

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

