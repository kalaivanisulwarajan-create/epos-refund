"""
Admin portal routes — for the internal Admin team to upload signed agreements.

  GET  /admin                        — list all requests awaiting document upload
  GET  /admin/upload/{request_id}    — upload form for a specific request
  POST /admin/upload/{request_id}    — handle file upload + signature verification
"""
import os
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database
from services import pdf_service     as pdf
from services import email_service   as em
from services import hubspot_service as hs

router    = APIRouter()
TEMPLATES = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)

BACKEND_URL  = os.getenv("BACKEND_URL", "http://localhost:8000")
UPLOAD_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "agreements")


# ── GET /admin ────────────────────────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
def admin_portal(request: Request):
    pending = database.get_pending_uploads()
    flash   = request.query_params.get("done")
    return TEMPLATES.TemplateResponse(
        "admin_portal.html",
        {"request": request, "requests": pending, "flash": flash},
    )


# ── GET /admin/upload/{request_id} ───────────────────────────────────────────

@router.get("/admin/upload/{request_id}", response_class=HTMLResponse)
def admin_upload_form(request_id: str, request: Request):
    row = database.get_by_id(request_id)
    if not row or row["status"] != "director_approved":
        return TEMPLATES.TemplateResponse(
            "error.html",
            {"request": request, "message": "Request not found or not awaiting upload."},
            status_code=404,
        )
    return TEMPLATES.TemplateResponse(
        "admin_upload.html",
        {"request": request, "refund_request": row},
    )


# ── POST /admin/upload/{request_id} ──────────────────────────────────────────

@router.post("/admin/upload/{request_id}", response_class=HTMLResponse)
async def admin_upload_submit(request_id: str, request: Request, file: UploadFile = File(...)):
    row = database.get_by_id(request_id)
    if not row or row["status"] != "director_approved":
        return TEMPLATES.TemplateResponse(
            "error.html",
            {"request": request, "message": "Request not found or not awaiting upload."},
            status_code=404,
        )

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        return TEMPLATES.TemplateResponse(
            "admin_upload.html",
            {
                "request":        request,
                "refund_request": row,
                "form_error":     "Only PDF files are accepted. Please upload a PDF.",
            },
        )

    # Save to temp path first for verification
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    tmp_path  = os.path.join(UPLOAD_DIR, f"tmp_{request_id}.pdf")
    final_path = os.path.join(UPLOAD_DIR, f"RDA_{request_id}.pdf")

    try:
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        return TEMPLATES.TemplateResponse(
            "admin_upload.html",
            {
                "request":        request,
                "refund_request": row,
                "form_error":     f"File save failed: {exc}",
            },
        )

    # Verify signature
    if not pdf.verify_signature(tmp_path):
        os.remove(tmp_path)
        return TEMPLATES.TemplateResponse(
            "admin_upload.html",
            {
                "request":        request,
                "refund_request": row,
                "form_error": (
                    "No signature detected in this document. "
                    "Please ensure the Return & Deposit Agreement has been signed "
                    "before uploading."
                ),
            },
        )

    # Move to final path
    os.replace(tmp_path, final_path)

    uploaded_at = datetime.now(timezone.utc).isoformat()

    # Update DB
    database.mark_document_uploaded(request_id, final_path, uploaded_at)

    # Refresh row
    row = database.get_by_id(request_id)

    # Update HubSpot: refund_status -> Approved
    deal_id = row.get("hs_deal_id") or row["deal_id"]
    hs.patch_deal(deal_id, {"refund_status": "Approved"})

    # Email BD + Finance
    download_url = f"{BACKEND_URL}/api/download/{request_id}"
    try:
        em.send_document_ready_notification(row, download_url)
    except Exception as exc:
        print(f"[Email] BD notification failed: {exc}")
    try:
        em.send_finance_notification(row, download_url)
    except Exception as exc:
        print(f"[Email] Finance notification failed: {exc}")

    return RedirectResponse(url=f"/admin?done={row['deal_name']}", status_code=303)
