"""
FastAPI entry point for the EPOS Refund System.

Run locally:
    cd backend
    uvicorn main:app --reload --port 8000
"""
import os
from dotenv import load_dotenv

# Load .env before anything else so all os.getenv() calls see the values
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database
from routes.refund   import router as refund_router
from routes.approval import router as approval_router
from routes.hardware import router as hardware_router
from routes.admin    import router as admin_router

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "EPOS Refund System",
    description = "Backend for the Sales Rep refund request → Director approval flow.",
    version     = "1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins     = [FRONTEND_URL, "http://localhost:5173", "http://localhost:4173"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Static files (signature image lives here) ─────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(refund_router)
app.include_router(approval_router)
app.include_router(hardware_router)
app.include_router(admin_router)

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    database.init_db()
    print("✅  Database initialised")
    print(f"✅  CORS allowing: {FRONTEND_URL}")
    _warn_missing_env()


def _warn_missing_env():
    required = [
        "HUBSPOT_TOKEN",
        "GMAIL_SENDER",
        "GMAIL_APP_PASSWORD",
        "DIRECTOR_EMAIL",
        "ADMIN_EMAIL",
        "FINANCE_EMAIL",
    ]
    missing = [k for k in required if not os.getenv(k) or os.getenv(k, "").startswith("your_")]
    if missing:
        print(f"⚠️   Missing / placeholder env vars: {', '.join(missing)}")
        print("    → Fill in backend/.env before testing live integrations.")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "epos-refund-backend"}
