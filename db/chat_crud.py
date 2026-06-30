from typing import Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from db.connection import db
from models.chat import ChatMessage, SessionResponse, SessionListItem

chat_collection: AsyncIOMotorCollection[dict[str, Any]] = db["chat_sessions"]

SYSTEM_PROMPT = "You are a helpful assistant. Answer questions clearly and concisely."


async def create_session(email: str) -> str:
    session_id = str(uuid4())
    now = datetime.now(timezone.utc)
    await chat_collection.insert_one({
        "session_id": session_id,
        "email": email,
        "title": "New Chat",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "created_at": now,
        "updated_at": now,
    })
    return session_id


async def get_sessions_by_email(email: str) -> list[SessionListItem]:
    cursor: AsyncIOMotorCursor[dict[str, Any]] = chat_collection.find(
        {"email": email},
        {"session_id": 1, "title": 1, "messages": 1, "created_at": 1, "updated_at": 1},
    ).sort("updated_at", -1)

    items: list[SessionListItem] = []
    async for doc in cursor:
        messages: list[dict[str, Any]] = doc.get("messages", [])
        non_system = [m for m in messages if m["role"] != "system"]
        user_msgs = [m for m in non_system if m["role"] == "user"]
        preview: str = user_msgs[0]["content"][:100] if user_msgs else ""
        items.append(SessionListItem(
            session_id=doc["session_id"],
            title=doc.get("title", "New Chat"),
            preview=preview,
            message_count=len(non_system),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        ))
    return items


async def get_session(session_id: str) -> Optional[SessionResponse]:
    doc: Optional[dict[str, Any]] = await chat_collection.find_one(
        {"session_id": session_id}
    )
    if not doc:
        return None
    return SessionResponse(
        session_id=doc["session_id"],
        email=doc.get("email", ""),
        title=doc.get("title", "New Chat"),
        messages=[ChatMessage(**m) for m in doc["messages"] if m["role"] != "system"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def get_messages_for_openai(session_id: str) -> Optional[list[dict[str, str]]]:
    doc: Optional[dict[str, Any]] = await chat_collection.find_one(
        {"session_id": session_id}
    )
    if not doc:
        return None
    return [{"role": m["role"], "content": m["content"]} for m in doc["messages"]]


async def append_messages(session_id: str, user_msg: str, assistant_msg: str) -> None:
    meta: Optional[dict[str, Any]] = await chat_collection.find_one(
        {"session_id": session_id}, {"title": 1}
    )
    set_fields: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if meta and meta.get("title") == "New Chat":
        set_fields["title"] = user_msg[:60].strip() + ("..." if len(user_msg) > 60 else "")

    await chat_collection.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": assistant_msg},
                    ]
                }
            },
            "$set": set_fields,
        },
    )


async def delete_session(session_id: str) -> bool:
    result = await chat_collection.delete_one({"session_id": session_id})
    return result.deleted_count == 1


async def clear_session_history(session_id: str) -> bool:
    result = await chat_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
                "title": "New Chat",
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return result.matched_count == 1


async def get_session_email(session_id: str) -> Optional[str]:
    doc = await chat_collection.find_one({"session_id": session_id}, {"email": 1})
    return doc.get("email") if doc else None


async def delete_message_at_index(session_id: str, msg_index: int) -> bool:
    doc = await chat_collection.find_one({"session_id": session_id}, {"messages": 1})
    if not doc:
        return False
    messages = list(doc["messages"])
    non_system = [(i, m) for i, m in enumerate(messages) if m.get("role") != "system"]
    if msg_index < 0 or msg_index >= len(non_system):
        return False
    global_index = non_system[msg_index][0]
    messages.pop(global_index)
    await chat_collection.update_one(
        {"session_id": session_id},
        {"$set": {"messages": messages, "updated_at": datetime.now(timezone.utc)}},
    )
    return True


async def update_session_title(session_id: str, title: str) -> bool:
    result = await chat_collection.update_one(
        {"session_id": session_id},
        {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
    )
    return result.matched_count == 1


async def delete_sessions_by_email(email: str) -> int:
    result = await chat_collection.delete_many({"email": email})
    return result.deleted_count


async def count_all_sessions() -> int:
    return await chat_collection.count_documents({})
