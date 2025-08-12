# 🚀 Streamlit App with Azure AD Login + Request Access Workflow

This project provides a secure and reusable **Azure AD OAuth login system** integrated into a **Streamlit app** using the MSAL Python SDK, with a built-in **Request Access** workflow that sends an email to approvers via **Microsoft Graph** if the signed-in user is not allow-listed.

---

## 📁 Folder Structure


```
your-project/
├── main_app.py # Main Streamlit App Logic (post-login, agent integration)
├── login_handler.py # Reusable login/auth + request access module
├── requirements.txt # Python dependencies
├── .env # Secure environment variables (not committed)
└── README.md
```


---

## ✅ Features

### 🔐 Login & Session Management (`login_handler.py`)
- Microsoft Azure AD OAuth 2.0 login using MSAL
- Session timeout control (default: 1 hour)
- Beautiful login page UI (custom fonts, hover effects)
- Secure token storage in `st.session_state`

### 🛡️ User-Level Authentication
- Restrict access to specific users by:
  - Storing allowed email addresses in `ALLOWED_USERS` (from `.env`)
  - OR integrating with a backend source (Azure Table Storage, DB)
- Unauthorized users are **not blocked outright** — they are shown the **Request Access** page

### 📩 Request Access Workflow
- If a logged-in user is **not allow-listed**:
  - Show “Access Denied” message
  - Prefill sender mailbox with the signed-in email (editable)
  - On submit, send a **prefilled access request email** to the configured approver/DL via **Microsoft Graph Mail.Send (Application)** using the **same Azure AD app credentials**
- Works with any mailbox your app is permitted to send as (service account or user account)

### 🧠 Main App (`app_main.py`)
- Prompt input interface powered by **LangGraph ReAct Agent** + **Azure OpenAI**
- Dynamic tool loading from your **MCP Server** via `MultiServerMCPClient`
- Sidebar listing available tools (fetched live from MCP)
- Executes user prompts with selected tools and returns AI responses

---

## 🧪 Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt

```env
# Azure AD (login + Graph mail send)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# App behaviour
AAD_REDIRECT_URI=http://localhost:8501
SESSION_TIMEOUT_SEC=3600
ALLOWED_USERS=guru.km@sonata-software.com,rpa.uat.bot1@sonata-software.com

# Access request recipient
ACCESS_REQUEST_TO=hr-platform-owners@sonata-software.com

```

> ⚠️ **NEVER** commit `.env` to GitHub! Add `.env` to `.gitignore`.

### 3. Run the App

```bash
streamlit run main_app.py
```

---

## 🔁 Reusing Login in Other Streamlit Apps

You can reuse the login module (`login_handler.py`) in **any** other Streamlit app by adding these lines at the top:

```python
from login_handler import setup_session, handle_auth_flow, ensure_not_expired, render_login_page, render_request_access_page

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
```

Then continue writing your Streamlit app logic as usual.

---

## ☁️ Deploying to Azure Web Apps

### 1. Set Redirect URI in Azure Portal

Go to:
- Azure Active Directory → **App registrations**
- Select your app → **Authentication**
- Add this as a redirect URI:

```
https://<your-app-name>.azurewebsites.net
```

### 2. Set Environment Variables in Azure

Go to:
- Azure App Service → **Configuration** → **Application settings**
- Add these environment variables:

| Name                  | Value                                       |
| --------------------- | ------------------------------------------- |
| AZURE_TENANT_ID       | Your tenant ID                              |
| AZURE_CLIENT_ID       | Your app’s client ID                        |
| AZURE_CLIENT_SECRET   | Your app’s client secret                    |
| AAD_REDIRECT_URI      | `https://<your-app-name>.azurewebsites.net` |
| ALLOWED_USERS         | Comma-separated list of allow-listed emails |
| ACCESS_REQUEST_TO     | Approver or DL email address                |

### 3. Deploy to Azure

You can deploy using:
- GitHub Actions
- Azure CLI
- Azure Portal (zip upload)

Make sure your deployment includes the following files:
- `main_app.py`
- `login_handler.py`
- `requirements.txt`
- `.env` (for local only)

---

## 📜 License

This project is provided for educational and internal use only. Use at your own discretion.