# page with details of receipt
import streamlit as st
import os

st.title("🧾 Invoice / Receipt Detail")

# Session data
receipt_data = st.session_state.get("receipt_data")

if receipt_data is None:
    st.warning("No receipt loaded")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    import os

    st.subheader("Receipt Image")

    image_path = receipt_data.get("image_path")

    # FIX: convert to absolute path if needed
    if image_path and not os.path.isabs(image_path):
        image_path = os.path.join("/workspaces/ExpenseLens", image_path)

    if image_path and os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
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
    st.switch_page("app.py")