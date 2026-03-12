# Setup and Run — SSO Demo (Pillar 2)

This is the reference implementation for the [SSO Authentication guide](../blog.md). It consists of a FastAPI backend that validates Azure AD JWTs and a React frontend that handles the MSAL login flow.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Two Azure AD app registrations** — follow Steps 1–3 in [`blog.md`](../blog.md) to create them and retrieve the required IDs:
  - `TENANT_ID`
  - `BACKEND_CLIENT_ID` (the `agent-api` registration)
  - `FRONTEND_CLIENT_ID` (the `agent-spa` registration)

---

## Backend

```bash
cd backend

# 1. Copy the environment template and fill in your values
cp .env.template .env
# Edit .env and set AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
# The env $(grep ...) pattern loads .env without a dotenv loader
env $(grep -v '^#' .env | grep '=' | xargs) uvicorn main:app --reload --port 8000
```

The backend starts at **http://localhost:8000**.

Verify it is running:
```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

Verify it rejects unauthenticated requests:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
# 403 Forbidden — expected
```

---

## Frontend

```bash
cd frontend

# 1. Copy the environment template and fill in your values
cp .env.template .env
# Edit .env and set REACT_APP_AZURE_CLIENT_ID, REACT_APP_AZURE_TENANT_ID,
# REACT_APP_AZURE_BACKEND_CLIENT_ID

# 2. Install dependencies
npm install

# 3. Start the dev server
npm start
```

The frontend starts at **http://localhost:3000** and opens in your default browser. You will be redirected to Microsoft login on first visit.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `AZURE_AD_TENANT_ID` | Your Entra ID tenant ID |
| `AZURE_AD_CLIENT_ID` | The `agent-api` backend app registration client ID |
| `GROUP_ID_AGENT_USERS` | Object ID of the agent users security group (optional) |
| `GROUP_ID_AGENT_ADMINS` | Object ID of the agent admins security group (optional) |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `REACT_APP_AZURE_CLIENT_ID` | The `agent-spa` frontend app registration client ID |
| `REACT_APP_AZURE_TENANT_ID` | Your Entra ID tenant ID |
| `REACT_APP_AZURE_BACKEND_CLIENT_ID` | The `agent-api` backend app registration client ID |
| `REACT_APP_API_URL` | Base URL of the FastAPI backend |

---

## Common Issues

See the **Troubleshooting** section in [`../blog.md`](../blog.md) for solutions to:
- 401 token validation errors (issuer mismatch, audience mismatch)
- Admin consent screen on login
- Redirect URI mismatch
- Empty `groups` claim
