import streamlit as st
from database.database import save_feedback

# make sure user is logged in
if "user_id" not in st.session_state:
    st.warning("Please login first")

    if st.button("Go to Login"):
        st.switch_page("app.py")

    st.stop()


st.title("💬 Feedback")

st.write(
    """
    Help us improve ExpenseLens!
    Let us know about your experience using the receipt scanner and expense tracking features.
    """
)

st.divider()

with st.form("feedback_form"):

    rating = st.slider(
        "Rate your experience",
        min_value=1,
        max_value=5,
        value=5
    )

    comment = st.text_area(
        "Comments or suggestions",
        placeholder="Tell us what you liked or what could be improved..."
    )

    submitted = st.form_submit_button("Submit Feedback")


if submitted:
    try:
        save_feedback(
            rating,
            comment
        )

        st.success("Thank you for your feedback! ⭐")

        st.write(
            "Your rating:",
            "⭐" * rating
        )

    except Exception as e:
        st.error("Could not save feedback.")
        st.write(e)


st.divider()

if st.button("← Back to Upload Screen"):
    st.switch_page("pages/upload_receipt.py")