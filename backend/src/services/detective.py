"""Investigation logic for detecting revenue leakage"""
from typing import List, Dict, Tuple
from dateutil.relativedelta import relativedelta
import uuid
from datetime import date, datetime

from src.config import get_settings
from src.models import Finding
from src.tools import (
    load_plan,
    query_invoices,
    fx_convert,
    propose_make_good_invoice,
    propose_credit_memo,
)
from src.tools.data_loader import load_billing_plans, load_invoices, load_credit_memos

# Get settings
settings = get_settings()


def _generate_expected_invoice_dates(
    start_date: date,
    cadence: str,
    end_date: date = None
) -> List[date]:
    """Generate expected invoice dates based on cadence"""
    if end_date is None:
        end_date = date.today()
    
    expected_dates = []
    current_date = start_date
    
    while current_date <= end_date:
        expected_dates.append(current_date)
        
        if cadence == "Monthly":
            current_date = current_date + relativedelta(months=1)
        elif cadence == "Quarterly":
            current_date = current_date + relativedelta(months=3)
        elif cadence == "Annual":
            current_date = current_date + relativedelta(years=1)
        else:
            break
    
    return expected_dates


def _calculate_expected_invoice_amount(
    total_value: float,
    cadence: str
) -> float:
    """Calculate expected invoice amount per billing period"""
    if cadence == "Monthly":
        return total_value / 12
    elif cadence == "Quarterly":
        return total_value / 4
    elif cadence == "Annual":
        return total_value
    return 0


def investigate_customer(plan_id: str) -> Tuple[List[Finding], List[Dict]]:
    """
    Investigate a specific customer's billing plan using tool functions.
    
    This uses the tool functions to maintain consistency and avoid
    duplicating data access logic.
    """
    findings = []
    proposals = []
    
    # Use tool function to load plan
    plan_data = load_plan(plan_id)
    if not plan_data:
        return findings, proposals
    
    # Convert to proper types
    start_date = plan_data['start_date']
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date).date()
    
    customer_name = plan_data['customer_name']
    total_value = plan_data['total_value']
    currency = plan_data['currency']
    cadence = plan_data['cadence']
    
    # Use tool function to query invoices
    invoices = query_invoices(plan_id=plan_id)
    
    # Generate expected invoice dates
    expected_dates = _generate_expected_invoice_dates(start_date, cadence)
    expected_amount = _calculate_expected_invoice_amount(total_value, cadence)
    
    # Convert invoice issue dates to a set for quick lookup

    invoiced_dates = set()
    for inv in invoices:
        inv_date = inv['issue_date']
        if isinstance(inv_date, str):
            inv_date = datetime.fromisoformat(inv_date).date()
        invoiced_dates.add(inv_date)
    
    # Check for missing invoices
    for expected_date in expected_dates:
        if expected_date > date.today():
            break  # Don't flag future invoices as missing
        
        # Allow configurable tolerance for invoice dates
        found = False
        for inv_date in invoiced_dates:
            if abs((inv_date - expected_date).days) <= settings.invoice_date_tolerance_days:
                found = True
                break
        
        if not found:
            finding_id = f"FIND-{uuid.uuid4().hex[:8].upper()}"
            finding = Finding(
                finding_id=finding_id,
                customer_name=customer_name,
                plan_id=plan_id,
                issue_type="missing_invoice",
                severity="critical",
                expected=f"Invoice for {expected_date} (~{expected_amount:.2f} {currency})",
                actual="No invoice found",
                impact_amount=expected_amount,
                impact_currency=currency,
                description=f"Missing {cadence.lower()} invoice for {expected_date.strftime('%B %Y')}",
                evidence=f"Plan expects {cadence.lower()} billing starting {start_date}. No invoice found around {expected_date}."
            )
            findings.append(finding)
            
            # Create proposal using tool function
            proposal = propose_make_good_invoice(
                finding_id=finding_id,
                plan_id=plan_id,
                customer_name=customer_name,
                amount=expected_amount,
                currency=currency,
                reason=f"Missing {cadence.lower()} invoice for {expected_date.strftime('%B %Y')}"
            )
            proposals.append(proposal)
    
    # Check each invoice for amount and currency discrepancies
    for inv in invoices:
        inv_amount = inv['amount_invoiced']
        inv_currency = inv['currency']
        inv_date = inv['issue_date']
        if isinstance(inv_date, str):
            inv_date = datetime.fromisoformat(inv_date).date()
        
        # Check currency mismatch
        if inv_currency != currency:
            # Use tool function for currency conversion
            converted_amount = fx_convert(inv_amount, inv_currency, currency, inv_date)
            difference = converted_amount - expected_amount
            
            if abs(difference) > settings.min_amount_threshold:  # Configurable threshold
                finding_id = f"FIND-{uuid.uuid4().hex[:8].upper()}"
                
                if difference > 0:
                    # Overbilling
                    finding = Finding(
                        finding_id=finding_id,
                        customer_name=customer_name,
                        plan_id=plan_id,
                        issue_type="overbilling",
                        severity="warning",
                        expected=f"{expected_amount:.2f} {currency}",
                        actual=f"{inv_amount:.2f} {inv_currency} (= {converted_amount:.2f} {currency})",
                        impact_amount=abs(difference),
                        impact_currency=currency,
                        description=f"Invoice {inv['invoice_id']} overbilled due to currency conversion",
                        evidence=f"Billed {inv_amount} {inv_currency}, converted to {converted_amount:.2f} {currency}. Expected {expected_amount:.2f} {currency}. Overbilling: {difference:.2f} {currency}."
                    )
                    findings.append(finding)
                    
                    # Check if credit memo already exists
                    memos = load_credit_memos()
                    memo_exists = any(m.invoice_id == inv['invoice_id'] for m in memos)
                    
                    if not memo_exists:
                        # Create proposal using tool function
                        proposal = propose_credit_memo(
                            finding_id=finding_id,
                            plan_id=plan_id,
                            customer_name=customer_name,
                            invoice_id=inv['invoice_id'],
                            amount=abs(difference),
                            currency=currency,
                            reason=f"FX overbilling adjustment ({inv_currency}→{currency})"
                        )
                        proposals.append(proposal)
        
        # Check amount discrepancy (same currency)
        elif abs(inv_amount - expected_amount) > settings.min_amount_threshold:
            difference = inv_amount - expected_amount
            finding_id = f"FIND-{uuid.uuid4().hex[:8].upper()}"
            
            if difference < 0:
                # Underbilling
                finding = Finding(
                    finding_id=finding_id,
                    customer_name=customer_name,
                    plan_id=plan_id,
                    issue_type="underbilling",
                    severity="critical",
                    expected=f"{expected_amount:.2f} {currency}",
                    actual=f"{inv_amount:.2f} {currency}",
                    impact_amount=abs(difference),
                    impact_currency=currency,
                    description=f"Invoice {inv['invoice_id']} underbilled by {abs(difference):.2f} {currency}",
                    evidence=f"Expected {expected_amount:.2f} {currency} per {cadence.lower()} period. Invoice {inv['invoice_id']} only billed {inv_amount:.2f} {currency}. Shortfall: {abs(difference):.2f} {currency}."
                )
                findings.append(finding)
                
                # Create proposal using tool function
                proposal = propose_make_good_invoice(
                    finding_id=finding_id,
                    plan_id=plan_id,
                    customer_name=customer_name,
                    amount=abs(difference),
                    currency=currency,
                    reason=f"Underbilling correction for invoice {inv['invoice_id']}"
                )
                proposals.append(proposal)
    
    return findings, proposals


def investigate_all() -> Tuple[List[Finding], List[Dict]]:
    """
    Run full investigation across all billing plans.
    
    Note: This loads all plans directly for efficiency, but uses
    tool functions for individual plan investigation to maintain consistency.
    """
    all_findings = []
    all_proposals = []
    
    # Load all plans (only place we load directly for efficiency)
    plans = load_billing_plans()
    invoices = load_invoices()
    
    # Investigate each plan using the tool-based investigation function
    for plan in plans:
        findings, proposals = investigate_customer(plan.plan_id)
        all_findings.extend(findings)
        all_proposals.extend(proposals)
    
    # Detect orphan invoices (no plan_id)
    for inv in invoices:
        if not inv.plan_id or inv.plan_id.strip() == "":
            finding_id = f"FIND-{uuid.uuid4().hex[:8].upper()}"
            finding = Finding(
                finding_id=finding_id,
                customer_name=inv.customer_name,
                plan_id="",
                issue_type="orphan_invoice",
                severity="warning",
                expected="Invoice linked to billing plan",
                actual="No plan_id reference",
                impact_amount=inv.amount_invoiced,
                impact_currency=inv.currency,
                description=f"Invoice {inv.invoice_id} has no billing plan reference",
                evidence=f"Invoice {inv.invoice_id} for {inv.customer_name} ({inv.amount_invoiced} {inv.currency}) has empty plan_id. Requires manual review."
            )
            all_findings.append(finding)
            # No automatic proposal for orphans - requires manual review
    
    return all_findings, all_proposals


def get_investigation_summary(findings: List[Finding]) -> Dict:
    """Generate summary statistics from findings"""
    total_impact = 0
    by_severity = {"critical": 0, "warning": 0, "info": 0}
    by_type = {}
    
    for finding in findings:
        # Count by severity
        by_severity[finding.severity] += 1
        
        # Count by type
        if finding.issue_type not in by_type:
            by_type[finding.issue_type] = 0
        by_type[finding.issue_type] += 1
        
        # Sum impact (convert to USD for simplicity)
        if finding.impact_currency == "USD":
            total_impact += finding.impact_amount
    
    return {
        "total_findings": len(findings),
        "total_impact_usd": total_impact,
        "by_severity": by_severity,
        "by_type": by_type
    }
