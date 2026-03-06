import streamlit as st
from services.parser import parse_csv_transactions
from utils.helpers import save_transactions


def upload_statement_page():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("Please login first.")
        st.stop()

    st.title("📤 Upload Bank Statement (CSV)")

    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file is None:
        st.info("Upload a CSV bank statement to import transactions.")
        return

    if st.button("Import Transactions"):
        try:
            user_id = st.session_state.get("user_id")

            transactions = parse_csv_transactions(uploaded_file.read())
            inserted = save_transactions(user_id, transactions, source="csv")

            st.success(f"✅ {inserted} transactions saved to database.")

        except Exception as e:
            st.error(f"Import failed: {e}")