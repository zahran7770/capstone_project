import streamlit as st
from passlib.context import CryptContext

from database.db import SessionLocal
from database.models import User

# MUST match login.py
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def register_page():
    st.write("")  # keeps spacing consistent if you're using background/card styles elsewhere

    st.markdown(
        """
        <div style="
            text-align: center;
            color: #ffffff;
            font-weight: 900;
            font-size: 40px;
            margin-bottom: 12px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.65);
        ">
            📝 Create Account
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Use a form so Enter submits + clean UX
    with st.form("register_form"):
        username = st.text_input("Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

        submitted = st.form_submit_button("Register", use_container_width=True)

    # Back to login (no form submit)
    if st.button("Back to Login", use_container_width=True, key="back_to_login"):
        st.session_state["auth_page"] = "login"
        st.rerun()

    if not submitted:
        return

    # -----------------------
    # Validation
    # -----------------------
    username = (username or "").strip()
    email = (email or "").strip()

    if not username or not email or not password or not confirm:
        st.error("All fields are required.")
        return

    if password != confirm:
        st.error("Passwords do not match.")
        return

    # Optional: basic email format check
    if "@" not in email or "." not in email:
        st.error("Please enter a valid email address.")
        return

    # -----------------------
    # DB write
    # -----------------------
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            st.error("Username already exists.")
            return

        if db.query(User).filter(User.email == email).first():
            st.error("Email already exists.")
            return

        new_user = User(
            username=username,
            email=email,
            password=hash_password(password),
        )

        db.add(new_user)
        db.commit()

        st.success("Registration successful! Please login.")

        # Route back to login (controlled navigation)
        st.session_state["auth_page"] = "login"
        st.rerun()

    finally:
        db.close()