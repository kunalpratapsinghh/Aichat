from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from typing import Any, Optional
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from db.connection import db
from models.user import UserCreate, UserUpdate, UserResponse

users_collection: AsyncIOMotorCollection[dict[str, Any]] = db["users"]


def _to_response(doc: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        age=doc["age"],
        phone=doc["phone"],
        is_active=doc["is_active"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _parse_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        raise ValueError(f"Invalid id format: {id}")


async def create_user(payload: UserCreate) -> UserResponse:
    now = datetime.now(timezone.utc)
    doc: dict[str, Any] = {**payload.model_dump(), "created_at": now, "updated_at": now}
    result = await users_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_response(doc)


async def get_all_users(skip: int = 0, limit: int = 20) -> list[UserResponse]:
    cursor: AsyncIOMotorCursor[dict[str, Any]] = (
        users_collection.find().skip(skip).limit(limit)
    )
    return [_to_response(doc) async for doc in cursor]


async def get_user_by_id(id: str) -> Optional[UserResponse]:
    doc: Optional[dict[str, Any]] = await users_collection.find_one(
        {"_id": _parse_object_id(id)}
    )
    return _to_response(doc) if doc else None


async def get_user_by_email(email: str) -> Optional[UserResponse]:
    doc: Optional[dict[str, Any]] = await users_collection.find_one({"email": email})
    return _to_response(doc) if doc else None


async def update_user(id: str, payload: UserUpdate) -> Optional[UserResponse]:
    changes: dict[str, Any] = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not changes:
        return await get_user_by_id(id)
    changes["updated_at"] = datetime.now(timezone.utc)
    result: Optional[dict[str, Any]] = await users_collection.find_one_and_update(
        {"_id": _parse_object_id(id)},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    return _to_response(result) if result else None


async def replace_user(id: str, payload: UserCreate) -> Optional[UserResponse]:
    now = datetime.now(timezone.utc)
    doc: dict[str, Any] = {**payload.model_dump(), "updated_at": now}
    result: Optional[dict[str, Any]] = await users_collection.find_one_and_update(
        {"_id": _parse_object_id(id)},
        {"$set": doc},
        return_document=ReturnDocument.AFTER,
    )
    return _to_response(result) if result else None


async def delete_user(id: str) -> bool:
    result = await users_collection.delete_one({"_id": _parse_object_id(id)})
    return result.deleted_count == 1


async def delete_all_users() -> int:
    result = await users_collection.delete_many({})
    return result.deleted_count
