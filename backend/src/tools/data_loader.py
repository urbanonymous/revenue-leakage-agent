"""Data loading functions for JSON files"""
import json
from pathlib import Path
from typing import List
from datetime import datetime

from src.models import BillingPlan, Invoice, CreditMemo, ExchangeRate


# Data directory paths
# __file__ is at /app/src/tools/data_loader.py
# data is at /app/src/data, sandbox is at /app/sandbox
DATA_DIR = Path(__file__).parent.parent / "data"
SANDBOX_DIR = Path(__file__).parent.parent.parent / "sandbox"


def _convert_dates(data: dict, date_fields: List[str]) -> dict:
    """Convert date strings to datetime.date objects"""
    result = data.copy()
    for field in date_fields:
        if field in result and result[field]:
            if isinstance(result[field], str):
                result[field] = datetime.fromisoformat(result[field]).date()
    return result


def load_billing_plans() -> List[BillingPlan]:
    """Load and validate billing plans from JSON"""
    file_path = DATA_DIR / "billing_plans.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    plans = []
    for item in data:
        item = _convert_dates(item, ['start_date'])
        plans.append(BillingPlan(**item))
    
    return plans


def load_invoices() -> List[Invoice]:
    """Load and validate invoices from JSON"""
    file_path = DATA_DIR / "invoices.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    invoices = []
    for item in data:
        item = _convert_dates(item, ['issue_date', 'due_date'])
        invoices.append(Invoice(**item))
    
    return invoices


def load_credit_memos() -> List[CreditMemo]:
    """Load and validate credit memos from JSON"""
    file_path = DATA_DIR / "credit_memos.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    memos = []
    for item in data:
        item = _convert_dates(item, ['issue_date'])
        memos.append(CreditMemo(**item))
    
    return memos


def load_exchange_rates() -> List[ExchangeRate]:
    """Load and validate exchange rates from JSON"""
    file_path = DATA_DIR / "exchange_rates.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    rates = []
    for item in data:
        item = _convert_dates(item, ['date'])
        rates.append(ExchangeRate(**item))
    
    return rates


def load_sandbox_file(filename: str) -> List[dict]:
    """Load a sandbox JSON file"""
    file_path = SANDBOX_DIR / filename
    if not file_path.exists():
        return []
    
    with open(file_path, 'r') as f:
        return json.load(f)


def save_sandbox_file(filename: str, data: List[dict]):
    """Save data to a sandbox JSON file"""
    file_path = SANDBOX_DIR / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

