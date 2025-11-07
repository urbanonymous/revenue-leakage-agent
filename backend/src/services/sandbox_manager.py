"""Sandbox management for proposal tracking and audit logging"""
from typing import List, Dict, Optional
from datetime import datetime

from src.tools.data_loader import load_sandbox_file, save_sandbox_file
import uuid


class SandboxManager:
    """Manages sandbox files and audit logging"""
    
    def __init__(self):
        self.make_good_file = 'make_good_invoices.json'
        self.credit_memo_file = 'credit_memos.json'
        self.amendment_file = 'plan_amendments.json'
        self.audit_log_file = 'audit_log.json'
    
    def get_all_applied_actions(self) -> Dict[str, List[Dict]]:
        """Get all applied actions from sandbox files"""
        return {
            'make_good_invoices': load_sandbox_file(self.make_good_file),
            'credit_memos': load_sandbox_file(self.credit_memo_file),
            'plan_amendments': load_sandbox_file(self.amendment_file)
        }
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict]:
        """Get audit log entries, optionally limited to recent N entries"""
        log = load_sandbox_file(self.audit_log_file)
        
        # Sort by timestamp (most recent first)
        log_sorted = sorted(
            log,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        if limit:
            return log_sorted[:limit]
        
        return log_sorted
    
    def find_action_by_id(self, action_id: str) -> Optional[Dict]:
        """Find an action in the audit log by ID"""
        log = load_sandbox_file(self.audit_log_file)
        
        for entry in log:
            if entry.get('action_id') == action_id:
                return entry
        
        return None
    
    def find_proposal_by_id(self, proposal_id: str) -> Optional[Dict]:
        """Find a proposal in any sandbox file by proposal ID"""
        # Check make-good invoices
        make_goods = load_sandbox_file(self.make_good_file)
        for mg in make_goods:
            if mg.get('proposal_id') == proposal_id:
                return {
                    **mg,
                    'type': 'make_good_invoice',
                    'status': 'applied'
                }
        
        # Check credit memos
        memos = load_sandbox_file(self.credit_memo_file)
        for memo in memos:
            if memo.get('proposal_id') == proposal_id:
                return {
                    **memo,
                    'type': 'credit_memo',
                    'status': 'applied'
                }
        
        # Check amendments
        amendments = load_sandbox_file(self.amendment_file)
        for amd in amendments:
            if amd.get('proposal_id') == proposal_id:
                return {
                    **amd,
                    'type': 'plan_amendment',
                    'status': 'applied'
                }
        
        return None
    
    def clear_sandbox(self) -> Dict:
        """Clear all sandbox files (useful for testing)"""
        save_sandbox_file(self.make_good_file, [])
        save_sandbox_file(self.credit_memo_file, [])
        save_sandbox_file(self.amendment_file, [])
        save_sandbox_file(self.audit_log_file, [])
        
        return {
            'status': 'success',
            'message': 'All sandbox files cleared'
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about applied actions"""
        actions = self.get_all_applied_actions()
        audit_log = self.get_audit_log()
        
        total_make_goods = len(actions['make_good_invoices'])
        total_credit_memos = len(actions['credit_memos'])
        total_amendments = len(actions['plan_amendments'])
        
        # Calculate total recovered/adjusted amounts
        total_recovered = sum(
            mg.get('amount', 0) 
            for mg in actions['make_good_invoices']
        )
        
        total_credited = sum(
            cm.get('amount', 0)
            for cm in actions['credit_memos']
        )
        
        # Count applies vs rollbacks
        applies = sum(1 for entry in audit_log if entry.get('action_type') == 'apply')
        rollbacks = sum(1 for entry in audit_log if entry.get('action_type') == 'rollback')
        
        return {
            'total_actions': total_make_goods + total_credit_memos + total_amendments,
            'make_good_invoices': total_make_goods,
            'credit_memos': total_credit_memos,
            'plan_amendments': total_amendments,
            'total_recovered_usd': total_recovered,
            'total_credited_usd': total_credited,
            'net_impact_usd': total_recovered - total_credited,
            'audit_entries': len(audit_log),
            'applies': applies,
            'rollbacks': rollbacks
        }
    
    def validate_proposal(self, proposal: Dict) -> tuple[bool, Optional[str]]:
        """Validate a proposal before applying"""
        # Check required fields
        required_fields = ['proposal_id', 'proposal_type', 'customer_name', 'plan_id', 'reason']
        
        for field in required_fields:
            if field not in proposal:
                return False, f"Missing required field: {field}"
        
        # Check proposal type
        valid_types = ['make_good_invoice', 'credit_memo', 'plan_amendment']
        if proposal['proposal_type'] not in valid_types:
            return False, f"Invalid proposal type: {proposal['proposal_type']}"
        
        # Type-specific validation
        if proposal['proposal_type'] in ['make_good_invoice', 'credit_memo']:
            if 'amount' not in proposal or 'currency' not in proposal:
                return False, "Make-good invoices and credit memos require amount and currency"
            
            if proposal['amount'] <= 0:
                return False, "Amount must be positive"
        
        if proposal['proposal_type'] == 'credit_memo':
            if 'details' not in proposal or 'invoice_id' not in proposal['details']:
                return False, "Credit memos require invoice_id in details"
        
        if proposal['proposal_type'] == 'plan_amendment':
            if 'details' not in proposal or 'changes' not in proposal['details']:
                return False, "Plan amendments require changes in details"
        
        return True, None


# Global sandbox manager instance
_sandbox_manager = None


def get_sandbox_manager() -> SandboxManager:
    """Get the global sandbox manager instance"""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = SandboxManager()
    return _sandbox_manager

