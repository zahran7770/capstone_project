import streamlit as st

def limits_page():
    # Protect page
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("Please login first.")
        st.stop()

    st.title("📊 Spending Limits")

    # Example: show limits (replace with DB later)
    st.write("Set monthly spending limits for categories:")

    categories = ["Food", "Transport", "Bills", "Shopping"]

    for cat in categories:
        st.number_input(f"{cat} Limit ($)", min_value=0, key=f"limit_{cat}")

    if st.button("Save Limits"):
        st.success("Limits saved successfully! (DB integration coming soon)")