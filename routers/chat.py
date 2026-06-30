import json
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk

from services.llm_client import llm
from db.chat_crud import (
    create_session,
    get_session,
    get_sessions_by_email,
    get_messages_for_openai,
    get_session_email,
    append_messages,
    delete_session,
    clear_session_history,
    update_session_title,
)
from db.user_crud import get_user_by_email
from models.chat import (
    NewSessionRequest,
    SendMessageRequest,
    SendMessageResponse,
    SessionResponse,
    SessionListItem,
    NewSessionResponse,
    UpdateSessionTitleRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/provider")
async def get_provider():
    return {"provider": llm.provider, "model": llm.model}


@router.get("/validate")
async def validate_user(email: Annotated[str, Query(min_length=1)]):
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found. Please contact your admin.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Your account is inactive. Please contact your admin.")
    return {"valid": True}


@router.post("/sessions", response_model=NewSessionResponse, status_code=status.HTTP_201_CREATED)
async def new_session(payload: NewSessionRequest):
    user = await get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found. Please contact your admin.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Your account is inactive. Please contact your admin.")
    session_id = await create_session(payload.email)
    return NewSessionResponse(session_id=session_id, message="Session created. Start chatting!")


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(email: Annotated[str, Query(min_length=1)]):
    return await get_sessions_by_email(email)


@router.patch("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def update_title(session_id: str, payload: UpdateSessionTitleRequest):
    updated = await update_session_title(session_id, payload.title)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"session_id": session_id, "title": payload.title}


@router.post("/sessions/{session_id}/message", response_model=SendMessageResponse)
async def send_message(session_id: str, payload: SendMessageRequest):
    history = await get_messages_for_openai(session_id)
    if history is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    history.append({"role": "user", "content": payload.message})

    try:
        response = await llm.client.chat.completions.create(
            model=llm.model,
            messages=history,  # type: ignore[arg-type]
            max_tokens=1024,
            temperature=0.7,
        )
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"LLM error: {str(e)}")

    reply = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0,
    }
    await append_messages(session_id, payload.message, reply)
    return SendMessageResponse(session_id=session_id, reply=reply, usage=usage)


@router.post("/sessions/{session_id}/stream")
async def stream_message(session_id: str, payload: SendMessageRequest):
    email = await get_session_email(session_id)
    if email is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    user = await get_user_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Your account has been deactivated. Please contact your admin.")

    history = await get_messages_for_openai(session_id)
    if history is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    history.append({"role": "user", "content": payload.message})
    collected: list[str] = []

    async def generate():
        try:
            stream: AsyncStream[ChatCompletionChunk] = await llm.client.chat.completions.create(  # type: ignore[assignment]
                model=llm.model,
                messages=history,  # type: ignore[arg-type]
                stream=True,
                max_tokens=1024,
                temperature=0.7,
            )
            async for chunk in stream:
                content: str = chunk.choices[0].delta.content or ""
                if content:
                    collected.append(content)
                    yield f"data: {json.dumps({'content': content})}\n\n"

            await append_messages(session_id, payload.message, "".join(collected))
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error("Streaming error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_history(session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}/history", status_code=status.HTTP_200_OK)
async def clear_history(session_id: str):
    cleared = await clear_session_history(session_id)
    if not cleared:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"message": "Conversation history cleared"}


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(session_id: str):
    deleted = await delete_session(session_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
