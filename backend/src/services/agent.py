"""PydanticAI agent for revenue investigation"""
from typing import List, Dict, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from datetime import datetime

from src.config import get_settings
from src.tools import (
    load_plan,
    query_invoices,
    fx_convert,
    propose_make_good_invoice,
    propose_credit_memo,
    propose_plan_amendment,
    apply,
    rollback,
    get_all_proposals
)
from src.tools.data_loader import load_billing_plans

# Get settings
settings = get_settings()

# Set OpenAI API key as environment variable (required by PydanticAI)
import os
os.environ['OPENAI_API_KEY'] = settings.openai_api_key

# Initialize OpenAI model with configured settings
model = OpenAIModel(settings.openai_model)

# System prompt for the agent
SYSTEM_PROMPT = """You are an expert AI financial detective specializing in revenue leakage detection.

Your role is to:
1. Investigate billing plans and invoices to detect anomalies
2. Identify revenue leakage issues such as:
   - Missing invoices that should have been issued
   - Underbilling (invoiced less than contracted amount)
   - Overbilling (invoiced more than contracted amount, often due to FX issues)
   - Currency conversion errors
   - Orphan invoices with no contract reference
3. Propose appropriate corrective actions:
   - Make-good invoices to recover missed revenue
   - Credit memos for overbilling corrections
   - Plan amendments for contract changes
4. Apply approved proposals to fix issues
5. Explain your findings clearly with supporting evidence and calculations

You have access to tools to:
- Load billing plans and query invoices
- Perform currency conversions
- Create proposals for corrective actions (propose_make_good_invoice, propose_credit_memo, propose_plan_amendment)
- Apply proposals with user approval (apply_proposal)
- View all proposals (list_proposals)

When a user asks you to fix or apply a correction:
- Use the appropriate propose_* function to create a proposal
- Explain what the proposal will do
- If the user confirms, use apply_proposal to execute it
- Show the results

When explaining findings or answering questions:
- Be thorough and systematic
- Show your calculations
- Cite specific invoice IDs and amounts
- Explain the business impact
- Recommend clear next steps

Always be factual, precise, and helpful in your analysis.
"""


# Create the agent with configured retries
revenue_agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    retries=settings.openai_max_retries
)


# Register tools for the agent
@revenue_agent.tool
async def get_all_billing_plans(ctx: RunContext[None]) -> List[Dict]:
    """Load all billing plans with their contract details"""
    plans = load_billing_plans()
    return [
        {
            "plan_id": p.plan_id,
            "customer_name": p.customer_name,
            "total_value": p.total_value,
            "currency": p.currency,
            "cadence": p.cadence,  # Monthly, Quarterly, or Annual
            "start_date": p.start_date.isoformat(),
            "amends": p.amends,  # Reference to parent plan if this is an amendment
            "entitlements": p.entitlements,
            "notes": p.notes
        }
        for p in plans
    ]


@revenue_agent.tool
async def get_billing_plan(ctx: RunContext[None], plan_id: str) -> Dict:
    """Load a specific billing plan by ID with full details"""
    return load_plan(plan_id)


@revenue_agent.tool
async def search_invoices(
    ctx: RunContext[None],
    plan_id: Optional[str] = None,
    customer_name: Optional[str] = None
) -> List[Dict]:
    """Search for invoices with optional filters. Returns invoice details including amounts, dates, and currencies."""
    return query_invoices(plan_id=plan_id, customer_name=customer_name)


@revenue_agent.tool
async def convert_currency(
    ctx: RunContext[None],
    amount: float,
    from_currency: str,
    to_currency: str,
    date_str: str
) -> float:
    """Convert currency amount using exchange rate on a specific date. Use this to compare invoices in different currencies."""
    date_obj = datetime.fromisoformat(date_str).date()
    return fx_convert(amount, from_currency, to_currency, date_obj)


@revenue_agent.tool
async def create_make_good_invoice_proposal(
    ctx: RunContext[None],
    finding_id: str,
    plan_id: str,
    customer_name: str,
    amount: float,
    currency: str,
    reason: str
) -> Dict:
    """Create a proposal for a make-good invoice to recover missing revenue. Use this when invoices were not issued as expected."""
    return propose_make_good_invoice(finding_id, plan_id, customer_name, amount, currency, reason)


@revenue_agent.tool
async def create_credit_memo_proposal(
    ctx: RunContext[None],
    finding_id: str,
    plan_id: str,
    customer_name: str,
    invoice_id: str,
    amount: float,
    currency: str,
    reason: str
) -> Dict:
    """Create a proposal for a credit memo to correct overbilling. Use this when customers were charged more than they should have been."""
    return propose_credit_memo(finding_id, plan_id, customer_name, invoice_id, amount, currency, reason)


@revenue_agent.tool
async def create_plan_amendment_proposal(
    ctx: RunContext[None],
    finding_id: str,
    plan_id: str,
    customer_name: str,
    changes: Dict,
    reason: str,
    effective_date: str
) -> Dict:
    """Create a proposal to amend a billing plan. Use this when the contract itself needs updating (e.g. price change, entitlement update)."""
    date_obj = datetime.fromisoformat(effective_date).date()
    return propose_plan_amendment(finding_id, plan_id, customer_name, changes, reason, date_obj)


@revenue_agent.tool
async def list_proposals(ctx: RunContext[None]) -> List[Dict]:
    """List all proposals (both pending and applied). Use this to check what proposals exist."""
    return get_all_proposals()


@revenue_agent.tool
async def apply_proposal(ctx: RunContext[None], proposal_id: str) -> Dict:
    """Apply a pending proposal to fix the revenue issue. This will execute the corrective action. Only use this after user confirmation."""
    # First get the proposal
    all_proposals = get_all_proposals()
    proposal = None
    for p in all_proposals:
        if p['proposal_id'] == proposal_id:
            proposal = p
            break
    
    if not proposal:
        return {"error": f"Proposal {proposal_id} not found"}
    
    if proposal.get('status') == 'applied':
        return {"error": f"Proposal {proposal_id} has already been applied"}
    
    return apply(proposal)


class RevenueAgent:
    """Wrapper class for the PydanticAI revenue agent"""
    
    def __init__(self):
        self.agent = revenue_agent
    
    async def run_full_investigation(self) -> Dict:
        """
        Run a complete AI-powered investigation across all customers.
        The LLM agent will analyze billing plans and invoices to detect revenue leakage.
        """
        investigation_prompt = """You are conducting a comprehensive revenue leakage investigation.

Your task:
1. Use get_all_billing_plans() to retrieve all billing plans
2. For each billing plan, analyze:
   - Expected cadence (Monthly, Quarterly, Annual) - this is the billing frequency
   - Expected total_value and currency - this is the contracted amount
   - Use search_invoices() to find related invoices
   - Check for missing invoices based on cadence
   - Verify invoice amounts match plan total_value (or proportional amounts for partial periods)
   - Check for currency conversion issues using convert_currency()
   - Note: Plans with 'amends' field reference a parent plan (amendments)
3. Identify all revenue leakage issues:
   - Missing invoices (no invoice when one should exist based on cadence)
   - Underbilling (invoiced less than contracted total_value)
   - Overbilling (invoiced more than contracted, often FX issues)
   - Orphan invoices (invoices with no plan_id reference)

For each issue found:
1. Generate a unique finding_id (like "FIND-1001", "FIND-1002", etc.)
2. IMMEDIATELY create a proposal using the appropriate tool:
   - For missing invoices → use create_make_good_invoice_proposal
   - For overbilling → use create_credit_memo_proposal
   - For contract discrepancies → use create_plan_amendment_proposal
3. Document the finding with:
   - finding_id
   - customer_name
   - plan_id
   - issue_type (missing_invoice, underbilling, overbilling, orphan_invoice)
   - severity (critical, warning, info)
   - expected (what should have happened)
   - actual (what actually happened)
   - impact_amount (financial impact)
   - impact_currency (USD)
   - description (clear explanation)
   - evidence (supporting data)
   - proposal_id (from the tool call)

Today's date is 2025-11-06. Consider billing periods up to this date.

IMPORTANT: Proactively CREATE PROPOSALS for every issue using the tools. Don't just describe the issues.

After creating all proposals, return your analysis as a structured JSON with:
{
  "findings": [list of findings with proposal_ids],
  "summary": {
    "total_findings": count,
    "total_proposals_created": count,
    "total_impact_usd": total,
    "by_severity": {critical: X, warning: Y},
    "by_type": {missing_invoice: X, underbilling: Y, ...}
  }
}

Be thorough and investigate every billing plan systematically."""

        try:
            result = await self.agent.run(investigation_prompt)
            # Parse the LLM's structured response
            import json
            response_text = result.output
            
            # Extract JSON from the response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            investigation_result = json.loads(response_text)
            
            # Add empty proposals list (proposals are generated separately)
            investigation_result["proposals"] = []
            
            return investigation_result
        except Exception as e:
            print(f"Error in AI investigation: {str(e)}")
            # Fallback to returning error structure
            return {
                "findings": [],
                "proposals": [],
                "summary": {
                    "total_findings": 0,
                    "total_impact_usd": 0,
                    "by_severity": {"critical": 0, "warning": 0, "info": 0},
                    "by_type": {},
                    "error": str(e)
                }
            }
    
    async def investigate_specific_customer(self, plan_id: str) -> Dict:
        """
        Run an AI-powered investigation for a specific customer billing plan.
        """
        investigation_prompt = f"""Investigate billing plan {plan_id} for revenue leakage.

Steps:
1. Use get_billing_plan("{plan_id}") to get plan details
2. Use search_invoices(plan_id="{plan_id}") to find all related invoices
3. Analyze for:
   - Missing invoices based on billing frequency
   - Amount mismatches (under/overbilling)
   - Currency conversion issues
4. Return findings in JSON format with structure:
{{
  "plan_id": "{plan_id}",
  "findings": [list of findings with all required fields],
  "summary": {{summary statistics}}
}}

Today's date is 2025-11-06."""

        try:
            result = await self.agent.run(investigation_prompt)
            import json
            response_text = result.output
            
            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            investigation_result = json.loads(response_text)
            investigation_result["proposals"] = []
            
            return investigation_result
        except Exception as e:
            return {
                "plan_id": plan_id,
                "findings": [],
                "proposals": [],
                "summary": {"error": str(e)}
            }
    
    async def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Chat with the AI agent about revenue issues.
        The agent can use registered tools to look up data and answer questions.
        """
        try:
            # Build context message
            context_msg = ""
            if context:
                context_msg = f"\n\nContext: {context}"
            
            # Run the agent - it can now use tools
            result = await self.agent.run(message + context_msg)
            
            return result.output
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    async def chat_stream(self, message: str, context: Optional[Dict] = None):
        """
        Stream chat responses with visibility into tool calls and agent reasoning.
        Yields events as they happen.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[AGENT] chat_stream called with message: {message[:50]}...")
        
        try:
            # Build context message
            context_msg = ""
            if context:
                context_msg = f"\n\nContext: {context}"
            
            logger.info("[AGENT] Starting run_stream with agent")
            
            # Use run_stream for streaming responses
            async with self.agent.run_stream(message + context_msg) as result:
                logger.info("[AGENT] run_stream context entered, starting to iterate chunks")
                chunk_count = 0
                
                # Stream each event
                async for chunk in result.stream():
                    chunk_count += 1
                    chunk_type = type(chunk).__name__
                    logger.info(f"[AGENT] Chunk #{chunk_count}: type={chunk_type}")
                    
                    # Handle string chunks (text content from LLM)
                    if isinstance(chunk, str):
                        if chunk:  # Only yield non-empty strings
                            logger.info(f"[AGENT] String chunk (text): {chunk[:50]}...")
                            yield {
                                'type': 'text',
                                'content': chunk
                            }
                    # Handle object chunks with attributes
                    elif hasattr(chunk, 'content') and chunk.content:
                        logger.info(f"[AGENT] Object chunk with content: {chunk.content[:50]}...")
                        yield {
                            'type': 'text',
                            'content': chunk.content
                        }
                    elif hasattr(chunk, 'tool_name'):
                        logger.info(f"[AGENT] Tool call: {chunk.tool_name}")
                        yield {
                            'type': 'tool_call',
                            'tool_name': chunk.tool_name,
                            'args': str(chunk.args) if hasattr(chunk, 'args') else ''
                        }
                    elif hasattr(chunk, 'tool_result'):
                        logger.info(f"[AGENT] Tool result from: {chunk.tool_name if hasattr(chunk, 'tool_name') else 'unknown'}")
                        yield {
                            'type': 'tool_result',
                            'tool_name': chunk.tool_name if hasattr(chunk, 'tool_name') else '',
                            'result': str(chunk.tool_result)[:200] + '...' if len(str(chunk.tool_result)) > 200 else str(chunk.tool_result)
                        }
                    else:
                        logger.warning(f"[AGENT] Unknown chunk type: {chunk_type}, value: {str(chunk)[:100]}")
                
                logger.info(f"[AGENT] Finished streaming {chunk_count} chunks")
        except Exception as e:
            logger.error(f"[AGENT] Error in chat_stream: {str(e)}", exc_info=True)
            yield {
                'type': 'error',
                'content': f"Error: {str(e)}"
            }
    
    async def explain_finding(self, finding: Dict) -> str:
        """
        Get a natural language explanation of a finding.
        Uses the LLM to provide business-friendly explanations.
        """
        prompt = f"""Explain this revenue leakage finding in clear business terms:

Customer: {finding['customer_name']}
Issue Type: {finding['issue_type']}
Severity: {finding['severity']}
Expected: {finding['expected']}
Actual: {finding['actual']}
Impact: {finding['impact_amount']} {finding['impact_currency']}
Description: {finding['description']}
Evidence: {finding['evidence']}

Provide:
1. What happened (the issue)
2. Why it's a problem (business impact)
3. What should be done (recommendation)
"""
        
        try:
            result = await self.agent.run(prompt)
            return result.output
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def apply_proposal(self, proposal: Dict) -> Dict:
        """Apply a proposal to the sandbox"""
        return apply(proposal)
    
    def rollback_action(self, action_id: str) -> Dict:
        """Rollback an applied action"""
        return rollback(action_id)
    
    def get_proposals(self) -> List[Dict]:
        """Get all proposals from sandbox"""
        return get_all_proposals()


# Global agent instance
agent_instance = RevenueAgent()


def get_agent() -> RevenueAgent:
    """Get the global agent instance"""
    return agent_instance
