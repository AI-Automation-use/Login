from login_handler import setup_session, handle_auth_flow, render_login_page
import streamlit as st

setup_session()
handle_auth_flow()

if not st.session_state.logged_in:
    render_login_page()
    st.stop()