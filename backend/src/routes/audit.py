"""Audit and sandbox routes"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from src.services import get_sandbox_manager

router = APIRouter(prefix="/api", tags=["audit"])

sandbox = get_sandbox_manager()


@router.get("/audit-log")
async def get_audit_log(limit: Optional[int] = None):
    """Get audit log entries"""
    try:
        log = sandbox.get_audit_log(limit=limit)
        return {"audit_log": log}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-log/{action_id}")
async def get_action_details(action_id: str):
    """Get details of a specific action"""
    try:
        action = sandbox.find_action_by_id(action_id)
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        return action
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sandbox/stats")
async def get_sandbox_stats():
    """Get sandbox statistics"""
    try:
        stats = sandbox.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sandbox/actions")
async def get_all_actions():
    """Get all applied actions from sandbox"""
    try:
        actions = sandbox.get_all_applied_actions()
        return actions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sandbox/clear")
async def clear_sandbox():
    """Clear all sandbox files (development only)"""
    try:
        result = sandbox.clear_sandbox()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

