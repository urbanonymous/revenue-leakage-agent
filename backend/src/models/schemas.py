"""Pydantic models for data structures"""
from typing import Optional, List, Literal
from datetime import date, datetime
from pydantic import BaseModel, Field


class BillingPlan(BaseModel):
    """Billing plan/contract model"""
    plan_id: str
    customer_name: str
    total_value: float
    currency: str
    cadence: Literal["Monthly", "Quarterly", "Annual"]
    start_date: date
    entitlements: List[str]
    notes: str
    amends: Optional[str] = None  # References another plan_id if this is an amendment


class Invoice(BaseModel):
    """Invoice model"""
    invoice_id: str
    plan_id: str
    customer_name: str
    issue_date: date
    due_date: date
    amount_invoiced: float
    currency: str
    status: Literal["paid", "unpaid"]
    description: str


class CreditMemo(BaseModel):
    """Credit memo model"""
    memo_id: str
    plan_id: str
    invoice_id: str
    amount: float
    currency: str
    issue_date: date
    reason: str


class ExchangeRate(BaseModel):
    """Exchange rate model"""
    date: date
    from_currency: str
    to_currency: str
    rate: float


class Finding(BaseModel):
    """Investigation finding model"""
    finding_id: str
    customer_name: str
    plan_id: str
    issue_type: Literal[
        "missing_invoice",
        "underbilling",
        "overbilling",
        "currency_mismatch",
        "orphan_invoice",
        "amendment_issue"
    ]
    severity: Literal["critical", "warning", "info"]
    expected: Optional[str] = None
    actual: Optional[str] = None
    impact_amount: float
    impact_currency: str
    description: str
    evidence: str


class Proposal(BaseModel):
    """Corrective action proposal model"""
    proposal_id: str
    proposal_type: Literal["make_good_invoice", "credit_memo", "plan_amendment"]
    finding_id: str
    customer_name: str
    plan_id: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: str
    details: dict
    status: Literal["pending", "applied", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class AuditLogEntry(BaseModel):
    """Audit log entry model"""
    action_id: str
    action_type: Literal["apply", "rollback"]
    proposal_id: str
    proposal_type: str
    customer_name: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user: str = "system"


class MakeGoodInvoice(BaseModel):
    """Make-good invoice record"""
    invoice_id: str
    plan_id: str
    customer_name: str
    amount: float
    currency: str
    reason: str
    created_at: datetime = Field(default_factory=datetime.now)
    proposal_id: str


class AppliedCreditMemo(BaseModel):
    """Applied credit memo record"""
    memo_id: str
    plan_id: str
    invoice_id: Optional[str] = None
    amount: float
    currency: str
    reason: str
    created_at: datetime = Field(default_factory=datetime.now)
    proposal_id: str


class PlanAmendment(BaseModel):
    """Plan amendment record"""
    amendment_id: str
    plan_id: str
    customer_name: str
    changes: dict
    reason: str
    effective_date: date
    created_at: datetime = Field(default_factory=datetime.now)
    proposal_id: str

