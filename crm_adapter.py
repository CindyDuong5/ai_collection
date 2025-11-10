from typing import Dict, Any, Optional

def record_call_start(task_id: str, payload: Dict[str, Any]) -> None:
    print(f"[CRM] Call start for task {task_id}: {payload}")

def record_call_result(data: Dict[str, Any]) -> None:
    print(f"[CRM] Call result: {data}")

def resend_invoice(invoice_number: str, email: str) -> bool:
    print(f"[CRM] Resend invoice {invoice_number} to {email}")
    return True

def update_contact(account_id: Optional[str],
                   account_name: Optional[str],
                   new_contact: Dict[str, Any]) -> None:
    print(f"[CRM] Update contact for {account_id or account_name}: {new_contact}")

def log_inbound_call(data: Dict[str, Any]) -> None:
    print(f"[CRM] Inbound call log: {data}")
