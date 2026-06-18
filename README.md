# EPOS Refund Request System

Form-based refund management for Sales Representatives, with Director e-signature approval and HubSpot integration.

---

## Local Development Setup

### 1. Backend (FastAPI)

```bash
cd backend

# Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# → Open .env and fill in all values (HubSpot token, Gmail, Director email, etc.)

# (Optional) Add director's signature image
# Place a PNG file at:  backend/static/signature.png
# Recommended: ~400×120px, transparent background

# Start the server
uvicorn main:app --reload --port 8000
```

Backend runs at → http://localhost:8000  
API docs at    → http://localhost:8000/docs

---

### 2. Frontend (React + Vite)

```bash
# From the project root (epos-refund/)
npm install
npm run dev
```

Frontend runs at → http://localhost:5173

> The Vite dev server proxies all `/api/*` requests to `localhost:8000` automatically.

---

## Environment Variables (`backend/.env`)

| Variable | Description |
|---|---|
| `HUBSPOT_TOKEN` | HubSpot Private App token (scopes: deals read/write, files, notes) |
| `GMAIL_SENDER` | Gmail/Workspace address that sends emails |
| `GMAIL_APP_PASSWORD` | 16-char App Password (not your account password) |
| `DIRECTOR_EMAIL` | Sales Director's email — receives approval requests |
| `DIRECTOR_NAME` | Director's display name in emails |
| `FINANCE_EMAIL` | Finance team email — receives approved refund notifications |
| `FRONTEND_URL` | Frontend origin for CORS (`http://localhost:5173` locally) |
| `BACKEND_URL` | Backend base URL used in email links (`http://localhost:8000` locally) |

---

## How to get a Gmail App Password

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (required)
3. Go to **App Passwords** → Select app: *Mail* → Select device: *Other*
4. Copy the 16-character password into `GMAIL_APP_PASSWORD`

---

## Director Signature Image

Place the director's signature at `backend/static/signature.png`.

- Recommended size: ~400 × 120 px
- Transparent background (PNG)
- If the file is missing, a text placeholder is used instead

---

## HubSpot Setup

The system uses:
- **Pipeline:** Revenue Team SG (`2054237899`)
- **Stage → Refund Requested:** `3730777848`
- **Stage → Refunded:** `3695886040`

Make sure your Private App has these scopes:
- `crm.objects.deals.read`
- `crm.objects.deals.write`
- `crm.objects.notes.write`
- `files`

---

## Flow Summary

```
BD fills form
  → Backend saves request, updates HubSpot stage → Refund Requested
  → Director receives email with [Approve] / [Reject] links

Director Approves
  → Signed PDF generated (with signature stamp)
  → HubSpot deal → Refunded stage
  → PDF attached to HubSpot deal (as a note)
  → BD receives email with PDF + download link
  → Finance receives email with PDF

Director Rejects
  → BD receives rejection email with reason
  → Finance is NOT notified
```

---

## Production Deployment

| Service | Platform |
|---|---|
| Frontend | Vercel — set `VITE_API_BASE=https://your-railway-app.railway.app` |
| Backend | Railway — set all env vars in Railway dashboard |

Add your Railway backend URL to `FRONTEND_URL` in Railway env, and to Vercel's environment variables as `VITE_API_BASE`.
