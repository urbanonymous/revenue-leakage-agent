"""Proposals routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

from src.services import get_agent, get_sandbox_manager

router = APIRouter(prefix="/api/proposals", tags=["proposals"])

agent = get_agent()
sandbox = get_sandbox_manager()


class ProposalApplyRequest(BaseModel):
    proposal: Dict


@router.get("")
async def get_proposals():
    """Get all proposals (pending and applied)"""
    try:
        proposals = agent.get_proposals()
        return {"proposals": proposals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
async def apply_proposal(request: ProposalApplyRequest):
    """Apply a proposal to the sandbox"""
    try:
        # Validate proposal
        is_valid, error_msg = sandbox.validate_proposal(request.proposal)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Apply the proposal
        result = agent.apply_proposal(request.proposal)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback/{action_id}")
async def rollback_action(action_id: str):
    """Rollback an applied action"""
    try:
        result = agent.rollback_action(action_id)
        
        if result.get('status') == 'error':
            raise HTTPException(status_code=404, detail=result.get('message'))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

