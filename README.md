# Aichat

A FastAPI-based AI chat application with user management, session-based conversations, and support for both OpenAI and Ollama (local) as LLM providers.

## Features

- User management (create, read, update, delete) with MongoDB
- Chat sessions with full conversation history
- Streaming and non-streaming LLM responses (Server-Sent Events)
- Switchable LLM backend: OpenAI or Ollama
- Admin dashboard with usage stats
- Built-in static frontend for chat and admin

## Tech Stack

- **Framework:** FastAPI
- **Database:** MongoDB (via Motor — async driver)
- **LLM:** OpenAI API or Ollama (local)
- **Python:** 3.9+
- **Package manager:** uv

## Project Structure

```
fastapi-demo/
├── main.py              # App entry point, router registration, lifespan
├── routers/
│   ├── users.py         # User CRUD endpoints
│   ├── chat.py          # Chat session & messaging endpoints
│   └── admin.py         # Admin stats & management endpoints
├── db/
│   ├── connection.py    # MongoDB client setup
│   ├── user_crud.py     # User database operations
│   └── chat_crud.py     # Chat session database operations
├── models/              # Pydantic models
├── services/
│   └── llm_client.py    # LLM provider abstraction (OpenAI / Ollama)
├── static/
│   ├── index.html       # Chat UI
│   └── admin.html       # Admin UI
├── .env.example         # Environment variable template
└── pyproject.toml
```

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd fastapi-demo
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017/
DB_NAME=fastapi_demo

# Options: openai | ollama
LLM_PROVIDER=ollama

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

### 3. Run the server

```bash
uv run uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`.

## API Overview

### Users — `/users`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/` | Create a user |
| `GET` | `/users/` | List users (`skip`, `limit` query params) |
| `GET` | `/users/{id}` | Get user by ID |
| `PUT` | `/users/{id}` | Replace user |
| `PATCH` | `/users/{id}` | Partial update |
| `DELETE` | `/users/{id}` | Delete user |
| `DELETE` | `/users/` | Delete all users |

### Chat — `/chat`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/chat/provider` | Current LLM provider and model |
| `GET` | `/chat/validate?email=` | Validate user access |
| `POST` | `/chat/sessions` | Start a new session |
| `GET` | `/chat/sessions?email=` | List sessions for a user |
| `PATCH` | `/chat/sessions/{session_id}` | Update session title |
| `GET` | `/chat/sessions/{session_id}` | Get session history |
| `POST` | `/chat/sessions/{session_id}/message` | Send a message (blocking) |
| `POST` | `/chat/sessions/{session_id}/stream` | Send a message (SSE stream) |
| `DELETE` | `/chat/sessions/{session_id}/history` | Clear session history |
| `DELETE` | `/chat/sessions/{session_id}` | Delete session |

### Admin — `/admin`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/stats` | Total/active users and session count |
| `DELETE` | `/admin/users/{email}/sessions` | Delete all sessions for a user |
| `DELETE` | `/admin/sessions/{session_id}/messages/{msg_index}` | Delete a specific message |

### Other

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | Chat UI |
| `GET` | `/admin` | Admin UI |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |
