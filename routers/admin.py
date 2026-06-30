from fastapi import APIRouter, HTTPException, status
from db.chat_crud import delete_sessions_by_email, count_all_sessions, delete_message_at_index
from db.user_crud import get_all_users

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats():
    users = await get_all_users(limit=10000)
    active = sum(1 for u in users if u.is_active)
    sessions = await count_all_sessions()
    return {"total_users": len(users), "active_users": active, "total_sessions": sessions}


@router.delete("/users/{email}/sessions", status_code=status.HTTP_200_OK)
async def bulk_delete_user_sessions(email: str):
    count = await delete_sessions_by_email(email)
    return {"deleted": count}


@router.delete("/sessions/{session_id}/messages/{msg_index}", status_code=status.HTTP_200_OK)
async def delete_session_message(session_id: str, msg_index: int):
    deleted = await delete_message_at_index(session_id, msg_index)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
    return {"deleted": True}
