# login_handler.py
import os
import msal
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# =========================
# Azure AD (user login) cfg
# =========================
CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["User.Read"]
REDIRECT_URI = os.getenv("AAD_REDIRECT_URI", "http://localhost:8501")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_SEC", "3600"))  # 1 hour default

# ==================================
# Simple allowlist (case-insensitive)
# ==================================
ALLOWED_USERS = [u.strip().lower() for u in filter(None, os.getenv("ALLOWED_USERS", "").split(","))] or [
    "guru.km@sonata-software.com",
    "rpa.uat.bot1@sonata-software.com",
]

# =======================================
# Microsoft Graph (app-only) mail sending
# =======================================
GRAPH_TENANT_ID = os.getenv("AZURE_TENANT_ID") or TENANT_ID
GRAPH_CLIENT_ID = os.getenv("AZURE_CLIENT_ID") or CLIENT_ID
GRAPH_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET") or CLIENT_SECRET
GRAPH_AUTHORITY = f"https://login.microsoftonline.com/{GRAPH_TENANT_ID}"
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# DL or approver mailbox to receive access requests
ACCESS_REQUEST_TO = os.getenv("ACCESS_REQUEST_TO", "guru.km@sonata-software.com")


# =================
# MSAL user helpers
# =================
def create_msal_app() -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )


def login_url() -> str:
    return create_msal_app().get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
        prompt="select_account",
    )


def _get_query_param(name: str):
    """
    Streamlit introduced st.query_params; older versions use experimental_get_query_params.
    This helper safely reads the code param.
    """
    try:
        # Streamlit >= 1.30
        qp = st.query_params
        return qp.get(name)
    except Exception:
        qp = st.experimental_get_query_params()
        vals = qp.get(name)
        return vals[0] if vals else None


def get_token_from_code(auth_code: str) -> dict:
    app = create_msal_app()
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
    )

    # Enrich claims for user email if MSAL didn't parse it
    if "id_token_claims" not in result:
        id_token = result.get("id_token")
        if id_token:
            try:
                import jwt
                result["id_token_claims"] = jwt.decode(id_token, options={"verify_signature": False})
            except Exception:
                pass
    return result


# =========================
# Microsoft Graph app-only
# =========================
def _graph_token() -> str:
    if not (GRAPH_TENANT_ID and GRAPH_CLIENT_ID and GRAPH_CLIENT_SECRET):
        raise RuntimeError(
            "Graph app-only creds missing: AZURE_AD_TENANT_ID / AZURE_AD_CLIENT_ID / AZURE_AD_CLIENT_SECRET"
        )
    app = msal.ConfidentialClientApplication(
        GRAPH_CLIENT_ID,
        authority=GRAPH_AUTHORITY,
        client_credential=GRAPH_CLIENT_SECRET,
    )
    res = app.acquire_token_for_client(scopes=GRAPH_SCOPE)
    if "access_token" not in res:
        raise RuntimeError(f"Graph token acquisition failed: {res}")
    return res["access_token"]


def _send_access_request_email(sender_user_id: str, requester_email: str):
    """
    Send a prefilled access-request email using /users/{sender}/sendMail (app-only).
    Only 'sender_user_id' is taken from UI; the rest is auto-filled.
    """
    token = _graph_token()

    subject = "Access Request: LangGraph AI Onboarding"
    html_body = f"""
    <p>Hello Team,</p>
    <p>The following user attempted to access the LangGraph AI Onboarding app and was blocked by the allowlist:</p>
    <ul>
      <li><b>Requester</b>: {requester_email}</li>
      <li><b>Attempt Time</b>: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</li>
      <li><b>Redirect URI</b>: {REDIRECT_URI}</li>
    </ul>
    <p>Please review and grant access if appropriate. Once approved, add the user to ALLOWED_USERS or the backing store.</p>
    <p>Thanks,<br/>AI-Automation Team</p>
    """

    payload = {
        "message": {
            "subject": subject,
            "importance": "Normal",
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": ACCESS_REQUEST_TO}}],
        },
        "saveToSentItems": True,
    }

    url = f"{GRAPH_BASE}/users/{sender_user_id}/sendMail"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if r.status_code != 202:
        raise RuntimeError(f"Send failed [{r.status_code}]: {r.text}")


# =====================
# Session state & login
# =====================
def setup_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.login_time = 0
    if "access_denied_email" not in st.session_state:
        st.session_state.access_denied_email = None


def handle_auth_flow():
    """
    Handles the auth code return. Sets either:
      - logged_in + token, or
      - access_denied_email (for request-access UI)
    """
    auth_code = _get_query_param("code")
    if auth_code and not st.session_state.logged_in:
        result = get_token_from_code(auth_code)

        if result and "access_token" in result:
            id_claims = result.get("id_token_claims", {}) or {}
            user_email = (id_claims.get("preferred_username") or id_claims.get("email") or "").lower()

            if not user_email:
                st.error("Login failed: Could not retrieve email from token.")
                return

            # Check allowlist
            if ALLOWED_USERS and user_email not in ALLOWED_USERS:
                st.session_state.access_denied_email = user_email
                return

            # Success
            st.session_state.logged_in = True
            st.session_state.token = result["access_token"]
            st.session_state.login_time = time.time()
            st.experimental_rerun()


def ensure_not_expired():
    if st.session_state.logged_in and time.time() - st.session_state.login_time > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.warning("Session expired. Please sign in again.")
        st.stop()


# ============
# UI fragments
# ============
def render_login_page():
    st.markdown(
        """
        <style>
        .login-header { text-align:center; font-size:32px; font-family:'Segoe UI', 'Poppins', sans-serif;
                        font-weight:600; margin-top:30px; margin-bottom:30px; }
        </style>
        <div class="login-header">🔐 Please sign in to continue</div>
        """,
        unsafe_allow_html=True,
    )

    url = login_url()
    st.markdown(
        f"""
        <style>
        .login-container {{ display:flex; flex-direction:column; align-items:center; margin-top:100px; }}
        .login-card {{ border:2px solid #e1e1e1; border-radius:12px; padding:30px 50px;
                       box-shadow:0 4px 12px rgba(0,0,0,0.1); transition:transform 0.2s; }}
        .login-card:hover {{ transform:scale(1.03); box-shadow:0 6px 16px rgba(0,0,0,0.15); }}
        .login-title {{ font-size:16px; margin-bottom:30px; display:flex; align-items:center; gap:10px; }}
        .login-img {{ width:250px; cursor:pointer; transition:transform 0.3s ease; }}
        .login-img:hover {{ transform:scale(1.05); }}
        </style>

        <div class="login-container">
            <div class="login-title">Click to Sign in with Microsoft</div>
            <div class="login-card">
                <a href="{url}">
                    <img class="login-img" src="https://cyberlab.co.uk/wp-content/uploads/2023/10/Microsoft_Top-Banner.png" alt="Microsoft Login" />
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_request_access_page():
    denied = (st.session_state.access_denied_email or "").lower() or "unknown@unknown"
    st.markdown(f"### 🚫 Access Denied for {denied}")
    st.write(
        "You don’t currently have access. You can request access below. "
        "The sender mailbox defaults to your signed-in email."
    )

    # Optional: allow a default service mailbox override via env
    default_sender = os.getenv("DEFAULT_SENDER_UPN", "").strip().lower() or denied

    with st.form("request_access_form", clear_on_submit=False):
        sender = st.text_input(
            "Sender mailbox to send the request from",
            value=default_sender,  # ← prefilled with login email (or DEFAULT_SENDER_UPN if set)
            help=(
                "This mailbox must be allowed for sending mails in OUTLOOK"
            ),
        )
        submitted = st.form_submit_button("📩 Request access")

    if submitted:
        senderr = (sender or "").strip()
        if not senderr:
            st.warning("Please enter a sender mailbox.")
            return
        try:
            _send_access_request_email(sender_user_id=senderr, requester_email=denied)
            st.success(f"Request sent from {senderr}. You’ll be notified after approval From CIO-Apps-Team.")
        except Exception as e:
            st.error(f"Failed to send request: {e}")

