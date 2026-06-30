from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers.users import router as users_router
from routers.chat import router as chat_router
from routers.admin import router as admin_router
from db.connection import client, users_collection
from db.chat_crud import chat_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the application...", app)
    # res = await client.server_info()
    # print(res)
    await users_collection.create_index("email", unique=True)
    await chat_collection.create_index("email")
    await chat_collection.create_index("session_id", unique=True)
    yield
    client.close()
    print("Shutting down the application...")


app = FastAPI(title="FastAPI Demo", version="1.0.0", lifespan=lifespan)

app.include_router(users_router)
app.include_router(chat_router)
app.include_router(admin_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/admin")
async def admin():
    return FileResponse("static/admin.html")
