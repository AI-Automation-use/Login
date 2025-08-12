from login_handler import setup_session, handle_auth_flow, ensure_not_expired, render_login_page, render_request_access_page
import streamlit as st

setup_session()
handle_auth_flow()
ensure_not_expired()

if not st.session_state.logged_in:
    if st.session_state.get("access_denied_email"):
        # User authenticated but not allowlisted → show Request Access flow
        render_request_access_page()
        st.stop()
    else:
        # Normal login screen
        render_login_page()
        st.stop()