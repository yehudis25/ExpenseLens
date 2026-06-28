# page with details of receipt
import streamlit as st

st.title("🧾 Invoice / Receipt Detail")

# Session data
receipt_image = st.session_state.get("uploaded_image")
receipt_data = st.session_state.get("receipt_data")

if receipt_data is None:
    st.warning("No receipt loaded")
    st.stop()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Receipt Image")

    if receipt_image:
        st.image(receipt_image, width="stretch")
    else:
        st.info("No receipt image available")

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

    if st.button("Delete Receipt"):
        # later: delete from database
        # 1. Execute a SQL query or database function to drop the text records
    # db.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))

    # 2. Call your cloud/file storage API to delete the image file instantly
    # storage.delete_file(receipt_image_path)
        st.session_state.pop("uploaded_image", None)
        st.session_state.pop("receipt_data", None)
        st.success("Deleted successfully!")
# Navigation Back Home
if st.button("← Back to Upload Screen"):
    st.switch_page("app.py")
