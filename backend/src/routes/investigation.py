"""Investigation routes"""
from fastapi import APIRouter, HTTPException

from src.services import get_agent

router = APIRouter(prefix="/api", tags=["investigation"])

agent = get_agent()


@router.post("/investigate")
async def investigate_all():
    """Run full investigation across all customers"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("[INVESTIGATION] Starting full investigation")
    try:
        result = await agent.run_full_investigation()
        logger.info(f"[INVESTIGATION] Completed with {len(result.get('findings', []))} findings")
        return result
    except Exception as e:
        logger.error(f"[INVESTIGATION] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigate/customer/{plan_id}")
async def investigate_customer(plan_id: str):
    """Investigate a specific customer by plan ID"""
    try:
        result = await agent.investigate_specific_customer(plan_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigate/by-name/{customer_name}")
async def investigate_by_customer_name(customer_name: str):
    """Investigate a specific customer by name"""
    try:
        # Map customer name to plan ID (get the main plan, not amendments)
        from src.tools.data_loader import load_billing_plans
        plans = load_billing_plans()
        
        # Find the plan for this customer (prefer non-amendment plans)
        customer_plan = None
        for plan in plans:
            if plan.customer_name == customer_name:
                # Prefer plans without amends (main contracts)
                if not plan.amends:
                    customer_plan = plan
                    break
                elif not customer_plan:
                    customer_plan = plan
        
        if not customer_plan:
            raise HTTPException(status_code=404, detail=f"No billing plan found for {customer_name}")
        
        result = await agent.investigate_specific_customer(customer_plan.plan_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def explain_finding(finding: dict):
    """Get natural language explanation of a finding"""
    try:
        explanation = await agent.explain_finding(finding)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

