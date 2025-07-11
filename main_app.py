# app_main.py
import streamlit as st
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from prompts import SYSTEM_PROMPT

from login_handler import setup_session, handle_auth_flow, render_login_page

# --------------------------
# Session & Authentication
# --------------------------
setup_session()
handle_auth_flow()

if not st.session_state.logged_in:
    render_login_page()
    st.stop()

# --------------------------
# Post-Login Application
# --------------------------
st.set_page_config(page_title="LangGraph AI Onboarding", layout="wide")
st.title("🤖 LangGraph AI Onboarding Agent")

@st.cache_resource
def load_mcp_tools():
    client = MultiServerMCPClient({
        "onboarding": {
            "url": "https://http-streamable-mcp-server.azurewebsites.net/mcp",
            "transport": "streamable_http"
        }
    })
    return asyncio.run(client.get_tools())

def load_chat_model():
    return AzureChatOpenAI(
        azure_endpoint="https://insightgen.openai.azure.com/",
        api_key="...",
        api_version="2024-05-01-preview",
        deployment_name="gpt-4o-mini",
        model="gpt-4o"
    )

def build_agent(tools):
    return create_react_agent(model=load_chat_model(), tools=tools, prompt=SYSTEM_PROMPT)

tools = load_mcp_tools()
st.sidebar.header("🛠️ Available Tools")
for tool in tools:
    st.sidebar.markdown(f"**{tool.name}**: {tool.description}")

user_prompt = st.text_area("💬 Enter your prompt:", height=150, placeholder="e.g., Create an email ID for John Doe...")

if st.button("🚀 Run Agent"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Thinking..."):
            agent = build_agent(tools)
            result = asyncio.run(agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]}))
            messages = result.get("messages", [])
            final_msg = next((m for m in reversed(messages) if isinstance(m, AIMessage) and m.content), None)

            if final_msg:
                st.success("✅ Agent Response:")
                st.markdown(final_msg.content)
            else:
                st.warning("No response received.")
