from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "fastapi_demo"

client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(MONGO_URI)
db: AsyncIOMotorDatabase[dict[str, Any]] = client[DB_NAME]

users_collection: AsyncIOMotorCollection[dict[str, Any]] = db["users"]
