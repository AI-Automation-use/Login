# login_handler.py
import os
import msal
import time
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
# Azure AD Config
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["User.Read"]
REDIRECT_URI = "http://localhost:8501"
SESSION_TIMEOUT = 3600  # 1 hour
ALLOWED_USERS = [
    "guru.km@sonata-software.com",
    "rpa.uat.bot1@sonata-software.com"
]
# MSAL helpers
def create_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

def login_url():
    return create_msal_app().get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
        prompt="select_account"
    )

def get_token_from_code(auth_code):
    app = create_msal_app()
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    if "id_token_claims" not in result:
        from msal.token_cache import TokenCache
        id_token = result.get("id_token")
        if id_token:
            import jwt
            result["id_token_claims"] = jwt.decode(id_token, options={"verify_signature": False})
    return result


# Session setup
def setup_session():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.login_time = 0

    # Check for session expiration
    if st.session_state.logged_in and time.time() - st.session_state.login_time > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.warning("Session expired. Please log in again.")
        st.stop()

# Process login if `?code=...` exists
def handle_auth_flow():
    auth_code = st.query_params.get("code")
    if auth_code and not st.session_state.logged_in:
        result = get_token_from_code(auth_code)

        if result and "access_token" in result:
            id_claims = result.get("id_token_claims", {})
            user_email = id_claims.get("preferred_username") or id_claims.get("email")

            if not user_email:
                st.error("Login failed: Could not retrieve email.")
                st.stop()

            if user_email.lower() not in [u.lower() for u in ALLOWED_USERS]:
                st.error(f"Access denied for user: {user_email}")
                st.stop()

            # All good
            st.session_state.logged_in = True
            st.session_state.token = result["access_token"]
            st.session_state.login_time = time.time()
            st.experimental_rerun()


# UI for login page
def render_login_page():

    st.markdown("""
        <style>
        .login-header {
            text-align: center;
            font-size: 32px;
            font-family: 'Segoe UI', 'Poppins', sans-serif;
            font-weight: 600;
            margin-top: 30px;
            margin-bottom: 30px;
        }
        </style>
        <div class="login-header">🔐 Please sign in to continue</div>
    """, unsafe_allow_html=True)

    url = login_url()
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 100px;
    }

    .login-card {
        border: 2px solid #e1e1e1;
        border-radius: 12px;
        padding: 30px 50px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }

    .login-card:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
    }

    .login-title {
        font-size: 16px;
        font-weight: italic;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .login-img {
        width: 250px;
        cursor: pointer;
        transition: transform 0.3s ease;
    }

    .login-img:hover {
        transform: scale(1.05);
    }
    </style>

    <div class="login-container">
        <div class="login-title">
            Click to Sign in with Microsoft
        </div>
        <div class="login-card">
            <a href='""" + url + """'>
                <img class="login-img" src="https://cyberlab.co.uk/wp-content/uploads/2023/10/Microsoft_Top-Banner.png" alt="Microsoft Login" />
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)
