import streamlit as st
from database.database import create_tables, DB_PATH
import os
import hashlib
import sqlite3

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

col1, col_center, col3 = st.columns([1, 2, 1])

with col_center:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=350)
    else:
        st.markdown("<h1 style='text-align: center;'>🔍</h1>", unsafe_allow_html=True)
    # st.markdown("<p style='text-align: center; color: gray; font-size: 1.15em;'>Precision Expense Tracking & Receipt Analysis</p>", unsafe_allow_html=True)

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
    if st.button("View Receipts"):
        st.switch_page("pages/summary.py")
    if st.button("View Budget Overview"):
        st.switch_page("pages/budget.py")


    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

