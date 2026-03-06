import streamlit as st
import base64
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from database.db import SessionLocal
from database.models import User

# Support both schemes (bcrypt + pbkdf2_sha256)
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def set_background():
    with open("assets/1.jpg", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                linear-gradient(rgba(17, 24, 39, 0.58), rgba(17, 24, 39, 0.58)),
                url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Form glass card */
        div[data-testid="stForm"] {{
            background-color: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.18);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            padding: 34px;
            border-radius: 16px;
            box-shadow: 0 18px 50px rgba(0,0,0,0.25);
        }}

        /* Buttons (Login + any other) */
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
            background-color: #4F46E5 !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            height: 44px !important;
            font-weight: 700 !important;
            border: 0 !important;
        }}
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
            filter: brightness(1.06);
        }}

        /* Labels & inputs */
        label, .stTextInput label {{
            color: rgba(255,255,255,0.92) !important;
        }}
        input {{
            border-radius: 10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_page():
    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "login"
    if "show_reset" not in st.session_state:
        st.session_state["show_reset"] = False

    set_background()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # White title banner (works even with light theme)
        st.markdown(
            """
            <div style="
                background: linear-gradient(90deg, rgba(17,24,39,0.78), rgba(31,41,55,0.65));
                border: 1px solid rgba(255,255,255,0.18);
                padding: 18px 14px;
                border-radius: 16px;
                text-align: center;
                margin-bottom: 16px;
                box-shadow: 0 14px 40px rgba(0,0,0,0.25);
            ">
                <div style="font-size:20px; font-weight:400; line-height:1.1; color:#ffffff;">
                    📊 Finance Tracker
                </div>
                <div style="font-size:15px; margin-top:6px; color: rgba(255,255,255,0.82);">
                    Track your spending. Stay in control.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # -----------------------
        # LOGIN FORM
        # -----------------------
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == username).first()

                if user and verify_password(password, user.password):
                    # Optional: upgrade hash if deprecated
                    if pwd_context.needs_update(user.password):
                        user.password = hash_password(password)
                        db.commit()

                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user.id
                    st.session_state["username"] = user.username
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            finally:
                db.close()

        # -----------------------
        # FORGOT PASSWORD (toggle)
        # -----------------------
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Forgot Password", use_container_width=True, key="toggle_reset"):
                st.session_state["show_reset"] = not st.session_state["show_reset"]
                st.rerun()
        with col_b:
            if st.button("Register", use_container_width=True, key="go_register"):
                st.session_state["auth_page"] = "register"
                st.rerun()

        if st.session_state["show_reset"]:
            st.markdown(
                "<div style='color:#ffffff; font-weight:800; margin-top:14px;'>Reset Password</div>",
                unsafe_allow_html=True,
            )
            with st.form("reset_form"):
                reset_username = st.text_input("Username", key="reset_username")
                new_password = st.text_input("New Password", type="password", key="reset_new_password")
                confirm_new = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
                reset_submit = st.form_submit_button("Update Password", use_container_width=True)

            if reset_submit:
                if not reset_username or not new_password or not confirm_new:
                    st.error("All fields are required.")
                elif new_password != confirm_new:
                    st.error("Passwords do not match.")
                else:
                    db = SessionLocal()
                    try:
                        u = db.query(User).filter(User.username == reset_username).first()
                        if not u:
                            st.error("User not found.")
                        else:
                            u.password = hash_password(new_password)
                            db.commit()
                            st.success("Password updated. You can now login.")
                            st.session_state["show_reset"] = False
                            st.rerun()
                    finally:
                        db.close()

        # White helper text
        st.markdown(
            """
            <div style="
                text-align:center;
                color:#ffffff;
                font-weight:500;
                margin-top:14px;
                font-size:15px;
                opacity:0.92;
            ">
                Don't have an account? Click Register above.
            </div>
            """,
            unsafe_allow_html=True,
        )