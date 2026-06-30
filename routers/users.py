import logging

from fastapi import APIRouter, HTTPException, Query, status
from typing import Annotated

logger = logging.getLogger(__name__)

from db.user_crud import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_email,
    update_user,
    replace_user,
    delete_user,
    delete_all_users,
)
from models.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: UserCreate):
    existing = await get_user_by_email(payload.email)
    logger = logging.getLogger("uvicorn.error")
    if existing:
        logger.error("Email already registered: %s", payload.email)
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    return await create_user(payload)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
):
    return await get_all_users(skip=skip, limit=limit)


@router.get("/{id}", response_model=UserResponse)
async def get_by_id(id: str):
    logger = logging.getLogger("uvicorn.error")
    try:
        user = await get_user_by_id(id)
    except ValueError:
        logger.error("Invalid user id: %s", id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
    if not user:
        logger.error("User not found please check the id: %s", id)  
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{id}", response_model=UserResponse)
async def replace(id: str, payload: UserCreate):
    try:
        user = await replace_user(id, payload)
    except ValueError:
        logger.error("Invalid user id: %s", id) 
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
    if not user:
        logger.error("User not found: %s", id)  
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{id}", response_model=UserResponse)
async def partial_update(id: str, payload: UserUpdate):
    try:
        user = await update_user(id, payload)
    except ValueError:
        logger.error("Invalid user id: %s", id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: str):
    try:
        deleted = await delete_user(id)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")


@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_all():
    count = await delete_all_users()
    return {"deleted": count}
