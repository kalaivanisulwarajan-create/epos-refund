"""
Approval / rejection routes — called by the Sales Director from email links.
Also serves the BD document download endpoint.

  GET  /api/approve/{token}        — Director clicks Approve
  GET  /api/reject/{token}         — Director clicks Reject  → shows reason form
  POST /api/reject/{token}         — Director submits rejection reason
  GET  /api/download/{request_id}  — BD downloads signed agreement
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

import database
from services import hubspot_service as hs
from services import email_service   as em

router    = APIRouter()
TEMPLATES = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# ── GET /api/approve/{token} ──────────────────────────────────────────────────

@router.get("/api/approve/{token}", response_class=HTMLResponse)
async def approve(token: str, request: Request):
    row = database.get_by_approve_token(token)

    if not row:
        return TEMPLATES.TemplateResponse(
            "error.html",
            {"request": request, "message": "Invalid or expired approval link."},
            status_code=404,
        )

    if row["status"] in ("director_approved", "document_ready"):
        return TEMPLATES.TemplateResponse(
            "already_actioned.html",
            {"request": request, "action": "approved", "deal_name": row["deal_name"]},
        )

    if row["status"] == "rejected":
        return TEMPLATES.TemplateResponse(
            "already_actioned.html",
            {"request": request, "action": "rejected", "deal_name": row["deal_name"]},
        )

    approved_at = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

    # 1. Mark Director approved in DB
    database.mark_director_approved(row["id"], datetime.now(timezone.utc).isoformat())

    # 2. Refresh row
    row = database.get_by_id(row["id"])

    # 3. Update HubSpot: status -> Under Review
    deal_id = row.get("hs_deal_id") or row["deal_id"]
    hs.patch_deal(deal_id, {"refund_status": hs.STATUS_UNDER_REVIEW})

    # 4. Notify Admin to prepare and upload the agreement
    try:
        em.send_admin_notification(row)
    except Exception as exc:
        print(f"[Email] admin notification failed: {exc}")

    return TEMPLATES.TemplateResponse(
        "approved.html",
        {
            "request":     request,
            "deal_name":   row["deal_name"],
            "sales_rep":   row["sales_rep_name"],
            "amount":      row["refund_amount"],
            "approved_at": approved_at,
        },
    )


# ── GET /api/reject/{token} ───────────────────────────────────────────────────

@router.get("/api/reject/{token}", response_class=HTMLResponse)
async def reject_form(token: str, request: Request):
    row = database.get_by_reject_token(token)

    if not row:
        return TEMPLATES.TemplateResponse(
            "error.html",
            {"request": request, "message": "Invalid or expired rejection link."},
            status_code=404,
        )

    if row["status"] in ("director_approved", "document_ready", "rejected"):
        return TEMPLATES.TemplateResponse(
            "already_actioned.html",
            {"request": request, "action": row["status"], "deal_name": row["deal_name"]},
        )

    return TEMPLATES.TemplateResponse(
        "reject_form.html",
        {
            "request":   request,
            "token":     token,
            "deal_name": row["deal_name"],
            "rep_name":  row["sales_rep_name"],
            "amount":    row["refund_amount"],
        },
    )


# ── POST /api/reject/{token} ──────────────────────────────────────────────────

@router.post("/api/reject/{token}", response_class=HTMLResponse)
async def reject_submit(token: str, request: Request, reason: str = Form(...)):
    reason = reason.strip()
    if not reason:
        row = database.get_by_reject_token(token)
        return TEMPLATES.TemplateResponse(
            "reject_form.html",
            {
                "request":    request,
                "token":      token,
                "deal_name":  row["deal_name"] if row else "",
                "rep_name":   row["sales_rep_name"] if row else "",
                "amount":     row["refund_amount"] if row else "",
                "form_error": "Please enter a reason before submitting.",
            },
            status_code=422,
        )

    row = database.get_by_reject_token(token)
    if not row:
        return TEMPLATES.TemplateResponse(
            "error.html",
            {"request": request, "message": "Invalid or expired rejection link."},
            status_code=404,
        )

    if row["status"] in ("director_approved", "document_ready", "rejected"):
        return TEMPLATES.TemplateResponse(
            "already_actioned.html",
            {"request": request, "action": row["status"], "deal_name": row["deal_name"]},
        )

    database.mark_rejected(row["id"], reason, datetime.now(timezone.utc).isoformat())

    deal_id = row.get("hs_deal_id") or row["deal_id"]
    hs.patch_deal(deal_id, {"refund_status": hs.STATUS_REJECTED})

    try:
        em.send_rejection_notification(row, reason)
    except Exception as exc:
        print(f"[Email] rejection notification failed: {exc}")

    return TEMPLATES.TemplateResponse(
        "rejected.html",
        {
            "request":   request,
            "deal_name": row["deal_name"],
            "rep_name":  row["sales_rep_name"],
            "reason":    reason,
        },
    )


# ── GET /api/download/{request_id} ───────────────────────────────────────────

@router.get("/api/download/{request_id}")
def download_document(request_id: str):
    row = database.get_by_id(request_id)

    if not row:
        raise HTTPException(status_code=404, detail="Request not found.")

    if row["status"] != "document_ready":
        raise HTTPException(
            status_code=403,
            detail="Document not yet available. It will be ready once Admin uploads the signed agreement.",
        )

    doc_path = row.get("uploaded_doc_path", "")
    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Document file not found on server.")

    filename = f"Return_Deposit_Agreement_{row['deal_name'].replace(' ', '_')[:40]}.pdf"
    return FileResponse(
        path       = doc_path,
        media_type = "application/pdf",
        filename   = filename,
    )
