from datetime import date
from typing import List, Optional, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from crm_adapter import (
    record_call_start,
    record_call_result,
    resend_invoice,
    update_contact,
    log_inbound_call,
)

# 🚨 This line MUST be top-level, no quotes before it, no indent:
app = FastAPI(title="Mainline AR Backend", version="1.0.0")

# ---------- Shared Schemas ----------

class InvoiceInfo(BaseModel):
    invoice_number: str
    amount: float
    due_date: Optional[date] = None
    days_overdue: Optional[int] = None
    description: Optional[str] = None


class ContactInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None  # e.g. "AP", "Owner"


class CallbackPreference(BaseModel):
    preferred_date: Optional[date] = None
    preferred_time_range: Optional[str] = None  # "9-11AM", etc.
    timezone: Optional[str] = None


# ---------- 1. (Optional) Call Start ----------

class CallStartPayload(BaseModel):
    task_id: str
    direction: Literal["outbound", "inbound"] = "outbound"
    to_phone: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    contact: Optional[ContactInfo] = None
    invoices: List[InvoiceInfo] = []
    metadata: dict = {}


@app.post("/vapi/call-start")
def vapi_call_start(payload: CallStartPayload):
    record_call_start(payload.task_id, payload.dict())
    return {"status": "ok"}


# ---------- 2. Call Result (Core Endpoint) ----------

class CallResultPayload(BaseModel):
    task_id: Optional[str] = None
    call_id: Optional[str] = None
    direction: Literal["outbound", "inbound"] = "outbound"

    outcome: Literal[
        "connected_right_person",
        "connected_wrong_person",
        "no_answer",
        "voicemail_left",
        "promise_to_pay",
        "dispute",
        "needs_invoice_resent",
        "callback_requested",
        "refused_to_pay",
        "other",
    ]
    outcome_detail: Optional[str] = None

    invoices: List[InvoiceInfo] = []
    promise_date: Optional[date] = None
    expected_payment_method: Optional[str] = None

    reason: Optional[str] = None

    confirmed_email: Optional[EmailStr] = None
    new_contact: Optional[ContactInfo] = None
    transfer_to_accounting: bool = False

    callback_preference: Optional[CallbackPreference] = None

    voicemail_left: bool = False

    notes: Optional[str] = None
    raw: Optional[dict] = None


@app.post("/vapi/call-result")
def vapi_call_result(payload: CallResultPayload):
    if payload.new_contact:
        update_contact(
            account_id=None,
            account_name=None,
            new_contact=payload.new_contact.dict(exclude_none=True),
        )

    data = payload.dict(exclude_none=True)
    record_call_result(data)

    return {"status": "ok"}


# ---------- 3. Resend Invoice ----------

class ResendInvoicePayload(BaseModel):
    invoice_number: str
    email: EmailStr
    requested_by: Optional[str] = "vapi"


@app.post("/vapi/resend-invoice")
def vapi_resend_invoice(payload: ResendInvoicePayload):
    success = resend_invoice(payload.invoice_number, payload.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to resend invoice")
    return {"status": "ok"}


# ---------- 4. Update Contact ----------

class UpdateContactPayload(BaseModel):
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    new_contact: ContactInfo


@app.post("/vapi/update-contact")
def vapi_update_contact(payload: UpdateContactPayload):
    if not (payload.account_id or payload.account_name):
        raise HTTPException(status_code=400, detail="Missing account identifier")

    update_contact(
        payload.account_id,
        payload.account_name,
        payload.new_contact.dict(exclude_none=True),
    )
    return {"status": "ok"}


# ---------- (Optional) Inbound Call Log ----------

class InboundCallLogPayload(BaseModel):
    from_phone: str
    reason: Optional[str] = None
    invoices: List[InvoiceInfo] = []
    callback_preference: Optional[CallbackPreference] = None
    notes: Optional[str] = None


@app.post("/vapi/inbound-log")
def vapi_inbound_log(payload: InboundCallLogPayload):
    log_inbound_call(payload.dict(exclude_none=True))
    return {"status": "ok"}


# ---------- Healthcheck ----------

@app.get("/health")
def health():
    return {"status": "ok"}
