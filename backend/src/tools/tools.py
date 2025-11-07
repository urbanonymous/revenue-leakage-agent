"""Tool functions for the AI agent"""
from typing import List, Dict, Optional
from datetime import date, datetime
import uuid

from .data_loader import (
    load_billing_plans,
    load_invoices,
    load_credit_memos,
    load_exchange_rates,
    load_sandbox_file,
    save_sandbox_file
)
from src.models import (
    BillingPlan,
    Invoice,
    CreditMemo,
    ExchangeRate,
    Proposal,
    AuditLogEntry,
    MakeGoodInvoice,
    AppliedCreditMemo,
    PlanAmendment
)


# Cache for loaded data
_data_cache = {
    'plans': None,
    'invoices': None,
    'memos': None,
    'rates': None
}


def _get_plans() -> List[BillingPlan]:
    """Get billing plans (cached)"""
    if _data_cache['plans'] is None:
        _data_cache['plans'] = load_billing_plans()
    return _data_cache['plans']


def _get_invoices() -> List[Invoice]:
    """Get invoices (cached)"""
    if _data_cache['invoices'] is None:
        _data_cache['invoices'] = load_invoices()
    return _data_cache['invoices']


def _get_credit_memos() -> List[CreditMemo]:
    """Get credit memos (cached)"""
    if _data_cache['memos'] is None:
        _data_cache['memos'] = load_credit_memos()
    return _data_cache['memos']


def _get_exchange_rates() -> List[ExchangeRate]:
    """Get exchange rates (cached)"""
    if _data_cache['rates'] is None:
        _data_cache['rates'] = load_exchange_rates()
    return _data_cache['rates']


def load_plan(plan_id: str) -> Optional[Dict]:
    """Load a specific billing plan by ID"""
    plans = _get_plans()
    for plan in plans:
        if plan.plan_id == plan_id:
            return plan.model_dump()
    return None


def query_invoices(
    plan_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict]:
    """Query invoices with optional filters"""
    invoices = _get_invoices()
    results = []
    
    for invoice in invoices:
        # Apply filters
        if plan_id and invoice.plan_id != plan_id:
            continue
        if customer_name and invoice.customer_name != customer_name:
            continue
        if start_date and invoice.issue_date < start_date:
            continue
        if end_date and invoice.issue_date > end_date:
            continue
        
        results.append(invoice.model_dump())
    
    return results


def fx_convert(
    amount: float,
    from_ccy: str,
    to_ccy: str,
    on_date: date
) -> float:
    """Convert currency amount using exchange rate on a specific date"""
    # If same currency, no conversion needed
    if from_ccy == to_ccy:
        return amount
    
    rates = _get_exchange_rates()
    
    # Find matching rate
    for rate in rates:
        if (rate.date == on_date and 
            rate.from_currency == from_ccy and 
            rate.to_currency == to_ccy):
            return amount * rate.rate
    
    # Rate not found, return original (or raise exception in production)
    return amount


def propose_make_good_invoice(
    finding_id: str,
    plan_id: str,
    customer_name: str,
    amount: float,
    currency: str,
    reason: str
) -> Dict:
    """Create a make-good invoice proposal"""
    proposal_id = f"PROP-MGI-{uuid.uuid4().hex[:8].upper()}"
    
    proposal = Proposal(
        proposal_id=proposal_id,
        proposal_type="make_good_invoice",
        finding_id=finding_id,
        customer_name=customer_name,
        plan_id=plan_id,
        amount=amount,
        currency=currency,
        reason=reason,
        details={
            "invoice_amount": amount,
            "invoice_currency": currency
        }
    )
    
    # Save proposal to sandbox
    proposal_dict = proposal.model_dump()
    proposals = load_sandbox_file('proposals.json')
    proposals.append(proposal_dict)
    save_sandbox_file('proposals.json', proposals)
    
    return proposal_dict


def propose_credit_memo(
    finding_id: str,
    plan_id: str,
    customer_name: str,
    invoice_id: str,
    amount: float,
    currency: str,
    reason: str
) -> Dict:
    """Create a credit memo proposal"""
    proposal_id = f"PROP-CM-{uuid.uuid4().hex[:8].upper()}"
    
    proposal = Proposal(
        proposal_id=proposal_id,
        proposal_type="credit_memo",
        finding_id=finding_id,
        customer_name=customer_name,
        plan_id=plan_id,
        amount=amount,
        currency=currency,
        reason=reason,
        details={
            "invoice_id": invoice_id,
            "credit_amount": amount
        }
    )
    
    # Save proposal to sandbox
    proposal_dict = proposal.model_dump()
    proposals = load_sandbox_file('proposals.json')
    proposals.append(proposal_dict)
    save_sandbox_file('proposals.json', proposals)
    
    return proposal_dict


def propose_plan_amendment(
    finding_id: str,
    plan_id: str,
    customer_name: str,
    changes: Dict,
    reason: str,
    effective_date: date
) -> Dict:
    """Create a plan amendment proposal"""
    proposal_id = f"PROP-AMD-{uuid.uuid4().hex[:8].upper()}"
    
    proposal = Proposal(
        proposal_id=proposal_id,
        proposal_type="plan_amendment",
        finding_id=finding_id,
        customer_name=customer_name,
        plan_id=plan_id,
        reason=reason,
        details={
            "changes": changes,
            "effective_date": str(effective_date)
        }
    )
    
    # Save proposal to sandbox
    proposal_dict = proposal.model_dump()
    proposals = load_sandbox_file('proposals.json')
    proposals.append(proposal_dict)
    save_sandbox_file('proposals.json', proposals)
    
    return proposal_dict


def apply(proposal: Dict) -> Dict:
    """Apply a proposal to the sandbox and log the action"""
    proposal_id = proposal['proposal_id']
    proposal_type = proposal['proposal_type']
    
    # Generate unique action ID
    action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
    
    # Remove from pending proposals
    proposals = load_sandbox_file('proposals.json')
    proposals = [p for p in proposals if p['proposal_id'] != proposal_id]
    save_sandbox_file('proposals.json', proposals)
    
    # Apply based on type
    if proposal_type == "make_good_invoice":
        # Create make-good invoice
        invoice_id = f"oiwef-MG-{uuid.uuid4().hex[:8].upper()}"
        make_good = MakeGoodInvoice(
            invoice_id=invoice_id,
            plan_id=proposal['plan_id'],
            customer_name=proposal['customer_name'],
            amount=proposal['amount'],
            currency=proposal['currency'],
            reason=proposal['reason'],
            proposal_id=proposal_id
        )
        
        # Save to sandbox
        invoices = load_sandbox_file('make_good_invoices.json')
        invoices.append(make_good.model_dump())
        save_sandbox_file('make_good_invoices.json', invoices)
        
    elif proposal_type == "credit_memo":
        # Create credit memo
        memo_id = f"M-CM-{uuid.uuid4().hex[:8].upper()}"
        credit_memo = AppliedCreditMemo(
            memo_id=memo_id,
            plan_id=proposal['plan_id'],
            invoice_id=proposal['details'].get('invoice_id'),
            amount=proposal['amount'],
            currency=proposal['currency'],
            reason=proposal['reason'],
            proposal_id=proposal_id
        )
        
        # Save to sandbox
        memos = load_sandbox_file('credit_memos.json')
        memos.append(credit_memo.model_dump())
        save_sandbox_file('credit_memos.json', memos)
        
    elif proposal_type == "plan_amendment":
        # Create plan amendment
        amendment_id = f"AMD-{uuid.uuid4().hex[:8].upper()}"
        amendment = PlanAmendment(
            amendment_id=amendment_id,
            plan_id=proposal['plan_id'],
            customer_name=proposal['customer_name'],
            changes=proposal['details']['changes'],
            reason=proposal['reason'],
            effective_date=datetime.fromisoformat(proposal['details']['effective_date']).date(),
            proposal_id=proposal_id
        )
        
        # Save to sandbox
        amendments = load_sandbox_file('plan_amendments.json')
        amendments.append(amendment.model_dump())
        save_sandbox_file('plan_amendments.json', amendments)
    
    # Create audit log entry
    audit_entry = AuditLogEntry(
        action_id=action_id,
        action_type="apply",
        proposal_id=proposal_id,
        proposal_type=proposal_type,
        customer_name=proposal['customer_name'],
        amount=proposal.get('amount'),
        currency=proposal.get('currency'),
        reason=proposal['reason']
    )
    
    # Save to audit log
    audit_log = load_sandbox_file('audit_log.json')
    audit_log.append(audit_entry.model_dump())
    save_sandbox_file('audit_log.json', audit_log)
    
    return {
        "action_id": action_id,
        "proposal_id": proposal_id,
        "status": "applied",
        "message": f"{proposal_type} applied successfully"
    }


def rollback(action_id: str) -> Dict:
    """Rollback an applied action"""
    # Load audit log
    audit_log = load_sandbox_file('audit_log.json')
    
    # Find the action
    action = None
    for entry in audit_log:
        if entry['action_id'] == action_id:
            action = entry
            break
    
    if not action:
        return {"status": "error", "message": "Action not found"}
    
    if action['action_type'] == 'rollback':
        return {"status": "error", "message": "Cannot rollback a rollback"}
    
    proposal_id = action['proposal_id']
    proposal_type = action['proposal_type']
    
    # Remove from appropriate sandbox file
    if proposal_type == "make_good_invoice":
        invoices = load_sandbox_file('make_good_invoices.json')
        invoices = [inv for inv in invoices if inv['proposal_id'] != proposal_id]
        save_sandbox_file('make_good_invoices.json', invoices)
        
    elif proposal_type == "credit_memo":
        memos = load_sandbox_file('credit_memos.json')
        memos = [memo for memo in memos if memo['proposal_id'] != proposal_id]
        save_sandbox_file('credit_memos.json', memos)
        
    elif proposal_type == "plan_amendment":
        amendments = load_sandbox_file('plan_amendments.json')
        amendments = [amd for amd in amendments if amd['proposal_id'] != proposal_id]
        save_sandbox_file('plan_amendments.json', amendments)
    
    # Create rollback audit entry
    rollback_entry = AuditLogEntry(
        action_id=f"ACT-RB-{uuid.uuid4().hex[:8].upper()}",
        action_type="rollback",
        proposal_id=proposal_id,
        proposal_type=proposal_type,
        customer_name=action['customer_name'],
        amount=action.get('amount'),
        currency=action.get('currency'),
        reason=f"Rollback of {action_id}"
    )
    
    audit_log.append(rollback_entry.model_dump())
    save_sandbox_file('audit_log.json', audit_log)
    
    return {
        "status": "rolled_back",
        "action_id": action_id,
        "message": f"Action {action_id} rolled back successfully"
    }


def get_all_proposals() -> List[Dict]:
    """Get all proposals (both pending and applied) from sandbox files"""
    all_proposals = []
    
    # Load pending proposals
    pending_proposals = load_sandbox_file('proposals.json')
    for prop in pending_proposals:
        prop['status'] = 'pending'
        all_proposals.append(prop)
    
    # Load all applied items from sandbox files
    make_goods = load_sandbox_file('make_good_invoices.json')
    credit_memos = load_sandbox_file('credit_memos.json')
    amendments = load_sandbox_file('plan_amendments.json')
    
    # Convert applied items to proposal format
    for mg in make_goods:
        all_proposals.append({
            'proposal_id': mg['proposal_id'],
            'proposal_type': 'make_good_invoice',
            'customer_name': mg['customer_name'],
            'plan_id': mg['plan_id'],
            'amount': mg['amount'],
            'currency': mg['currency'],
            'reason': mg['reason'],
            'status': 'applied',
            'created_at': mg['created_at']
        })
    
    for cm in credit_memos:
        all_proposals.append({
            'proposal_id': cm['proposal_id'],
            'proposal_type': 'credit_memo',
            'customer_name': 'N/A',
            'plan_id': cm['plan_id'],
            'amount': cm['amount'],
            'currency': cm['currency'],
            'reason': cm['reason'],
            'status': 'applied',
            'created_at': cm['created_at']
        })
    
    for amd in amendments:
        all_proposals.append({
            'proposal_id': amd['proposal_id'],
            'proposal_type': 'plan_amendment',
            'customer_name': amd['customer_name'],
            'plan_id': amd['plan_id'],
            'amount': None,
            'currency': None,
            'reason': amd['reason'],
            'status': 'applied',
            'created_at': amd['created_at']
        })
    
    return all_proposals

