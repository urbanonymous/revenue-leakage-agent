"""Chat routes"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
import json

from src.services import get_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

agent = get_agent()


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI agent about revenue issues"""
    try:
        response = await agent.chat(request.message, request.context)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses with tool call visibility"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[STREAM] Starting chat stream for message: {request.message[:50]}...")
    
    async def event_generator():
        try:
            logger.info("[STREAM] Entering event generator")
            event_count = 0
            async for event in agent.chat_stream(request.message, request.context):
                event_count += 1
                logger.info(f"[STREAM] Event #{event_count}: {event.get('type', 'unknown')}")
                # Send each event as JSON
                yield f"data: {json.dumps(event)}\n\n"
            # Send completion signal
            logger.info(f"[STREAM] Completed with {event_count} events, sending done signal")
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"[STREAM] Error in stream: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

