import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .db import init_db
from .schemas import CreateChatRequest, UpdateChatRequest
from .services.agent import stream_agent_reply
from .services.openai import openai
from .services.store import (
    add_message,
    create_chat,
    delete_chat,
    get_chat,
    list_chats,
    replace_last_assistant_message,
    update_chat,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Nexora Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/models")
async def models() -> list[dict]:
    model_list = await openai.list_models()
    print("[api/models] discovered models:", [model.get("name") for model in model_list], flush=True)
    return model_list


@app.get("/api/chats")
async def chats(search: str = ""):
    return list_chats(search)


@app.post("/api/chats")
async def create_chat_route(payload: CreateChatRequest):
    print("[api/chats] create", {"title": payload.title, "model": payload.model}, flush=True)
    return create_chat(payload.title, payload.model, payload.system_prompt)


@app.get("/api/chats/{chat_id}")
async def get_chat_route(chat_id: str):
    try:
        return get_chat(chat_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Chat not found") from exc


@app.patch("/api/chats/{chat_id}")
async def update_chat_route(chat_id: str, payload: UpdateChatRequest):
    try:
        return update_chat(chat_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Chat not found") from exc


@app.delete("/api/chats/{chat_id}")
async def delete_chat_route(chat_id: str):
    delete_chat(chat_id)
    return {"ok": True}


@app.post("/api/chats/{chat_id}/regenerate")
async def regenerate_route(chat_id: str):
    print("[api/chats/regenerate]", {"chat_id": chat_id}, flush=True)
    replace_last_assistant_message(chat_id)
    return get_chat(chat_id)


@app.post("/api/chat/stream")
async def chat_stream_route(payload: dict):
    print(
        "[api/chat/stream] incoming",
        {
            "chat_id": payload.get("chat_id"),
            "model": payload.get("model"),
            "message_count": len(payload.get("messages", [])),
        },
        flush=True,
    )
    chat_id = payload["chat_id"]
    if payload["messages"]:
        last = payload["messages"][-1]
        add_message(
            chat_id=chat_id,
            role=last["role"],
            content=last["content"],
            attachments=[{"file_id": file_id, "name": file_id} for file_id in last.get("attachments", [])],
        )

    async def event_stream():
        assistant_content = ""
        tool_events = []
        async for event in stream_agent_reply(payload):
            if event["type"] != "token":
                print("[api/chat/stream] event", event["type"], flush=True)
            if event["type"] == "token":
                assistant_content += event["data"]
            elif event["type"] == "tool_end":
                tool_events.append(event["data"])
            elif event["type"] == "done":
                data = event["data"]
                print(
                    "[api/chat/stream] done",
                    {"chat_id": chat_id, "response_length": len(data["content"]), "tool_events": len(data["tool_events"])},
                    flush=True,
                )
                add_message(chat_id=chat_id, role="assistant", content=data["content"], tool_events=data["tool_events"])
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
