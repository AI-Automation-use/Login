# 🚀 Streamlit App with Azure AD Login

This project provides a secure and reusable **Azure AD OAuth login system** integrated into a **Streamlit app** using the MSAL Python SDK.

---

## 📁 Folder Structure

```
your-project/
├── main_app.py        # Main Streamlit App Logic (post-login)
├── login_handler.py   # Reusable login/auth module
├── .env               # Secure env variables (not committed)
└── README.md
```

---

## ✅ Features

### 🔐 Login Features (from `login_handler.py`)
- Microsoft Azure AD OAuth 2.0 login using MSAL
- Session timeout control (default: 1 hour)
- Login page with:
  - Custom fonts and styles
  - Hover effects
- Secure token storage in `st.session_state`

### 🧠 Main App (from `app_main.py`)
- Prompt input interface using LangGraph + Azure OpenAI
- Dynamic tool loading via `MultiServerMCPClient`
- Sidebar showing available tools
- Handles prompt execution using LangChain agents

---

## 🧪 Running Locally

### 1. Install Dependencies

### 2. Create `.env` File

```env
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
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
from login_handler import setup_session, handle_auth_flow, render_login_page

setup_session()
handle_auth_flow()

if not st.session_state.logged_in:
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

| Name                | Value                                          |
|---------------------|------------------------------------------------|
| AZURE_CLIENT_ID     | Your app’s client ID                          |
| AZURE_CLIENT_SECRET | Your app’s client secret                      |
| AZURE_TENANT_ID     | Your Azure AD tenant ID                       |
### 3. Deploy to Azure

You can deploy using:
- GitHub Actions
- Azure CLI
- Azure Portal (zip upload)

Make sure your deployment includes the following files:
- `app_main.py`
- `login_handler.py`
- `requirements.txt`
- `.env` (for local only)

---

## 📜 License

This project is provided for educational and internal use only. Use at your own discretion.