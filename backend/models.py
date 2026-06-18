"""Pydantic models for request/response validation."""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal


class RefundRequestIn(BaseModel):
    """Payload the frontend sends when BD submits the form."""
    sales_rep_name:   str
    sales_rep_id:     str
    sales_rep_email:  str
    deal_id:          str
    deal_name:        str
    bank_name:        str
    account_no:       str
    refund_amount:    str   # keep as string; validated below
    refund_reason:    str
    refund_type:      Literal["full", "partial"]
    partial_products: str = ""

    @field_validator("refund_amount")
    @classmethod
    def must_be_numeric(cls, v: str) -> str:
        cleaned = v.replace(",", "").strip()
        try:
            float(cleaned)
        except ValueError:
            raise ValueError("refund_amount must be a valid number")
        return v

    @field_validator("sales_rep_name", "deal_id", "deal_name",
                     "bank_name", "account_no", "refund_reason")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v


class RefundRequestOut(BaseModel):
    """Response after successful form submission."""
    success:    bool
    request_id: str
    message:    str


class RejectPayload(BaseModel):
    """Body sent when Director submits the rejection form."""
    reason: str

    @field_validator("reason")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rejection reason is required")
        return v


class DealItem(BaseModel):
    """A HubSpot deal row returned to the frontend dropdown."""
    id:       str
    name:     str
    amount:   str
    stage:    str
    stage_id: str = ""   # raw HubSpot stage ID — used by frontend for card colour
