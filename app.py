import streamlit as st
from auth.login import login_page
from auth.register import register_page
from app_pages.dashboard import dashboard_page
from app_pages.upload_statement import upload_statement_page
from app_pages.limits import limits_page

from database.db import engine
from database.models import Base

Base.metadata.create_all(bind=engine)

# -----------------------
# SESSION INIT
# -----------------------

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 🔥 controls login/register switching
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "login"


# -----------------------
# IF NOT LOGGED IN
# -----------------------

if not st.session_state["logged_in"]:

    # Hide sidebar
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 🔥 Show correct auth page
    if st.session_state["auth_page"] == "register":
        register_page()
    else:
        login_page()


# -----------------------
# IF LOGGED IN
# -----------------------

else:

    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Upload Statement", "Limits", "Logout"]
    )

    if menu == "Dashboard":
        dashboard_page()
    elif menu == "Upload Statement":
        upload_statement_page()
    elif menu == "Limits":
        limits_page()
    elif menu == "Logout":
        st.session_state.clear()
        st.rerun()