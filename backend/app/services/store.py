from datetime import datetime, timezone
from uuid import uuid4

from ..db import decode_json, encode_json, get_conn
from ..schemas import ChatDetail, ChatSummary, Message


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_chat(title: str, model: str, system_prompt: str | None, client_id: str) -> ChatSummary:
    chat_id = str(uuid4())
    timestamp = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO chats(id, client_id, title, model, system_prompt, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (chat_id, client_id, title, model, system_prompt, timestamp, timestamp),
        )
    return get_chat(chat_id, client_id)


def list_chats(client_id: str, query: str = "") -> list[ChatSummary]:
    sql = """
        SELECT c.*,
               COALESCE(
                   (SELECT content FROM messages m WHERE m.chat_id = c.id ORDER BY m.created_at DESC LIMIT 1),
                   ''
               ) AS last_message
        FROM chats c
        WHERE c.client_id = ?
    """
    params: list[str] = [client_id]
    if query:
        sql += " AND (c.title LIKE ? OR EXISTS (SELECT 1 FROM messages m WHERE m.chat_id = c.id AND m.content LIKE ?))"
        like = f"%{query}%"
        params.extend([like, like])
    sql += " ORDER BY c.pinned DESC, c.updated_at DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [ChatSummary(**dict(row)) for row in rows]


def get_chat(chat_id: str, client_id: str) -> ChatDetail:
    with get_conn() as conn:
        chat = conn.execute(
            """
            SELECT c.*,
                   COALESCE(
                       (SELECT content FROM messages m WHERE m.chat_id = c.id ORDER BY m.created_at DESC LIMIT 1),
                       ''
                   ) AS last_message
            FROM chats c
            WHERE c.id = ? AND c.client_id = ?
            """,
            (chat_id, client_id),
        ).fetchone()
        messages = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,),
        ).fetchall()
    if not chat:
        raise KeyError(chat_id)
    payload = dict(chat)
    payload["messages"] = [
        Message(
            **{
                **dict(row),
                "tool_events": decode_json(row["tool_events"]),
                "attachments": decode_json(row["attachments"]),
            }
        )
        for row in messages
    ]
    return ChatDetail(**payload)


def update_chat(chat_id: str, client_id: str, **changes) -> ChatDetail:
    allowed = {key: value for key, value in changes.items() if value is not None}
    if allowed:
        fields = ", ".join([f"{key} = ?" for key in allowed] + ["updated_at = ?"])
        params = [*allowed.values(), now_iso(), chat_id, client_id]
        with get_conn() as conn:
            conn.execute(f"UPDATE chats SET {fields} WHERE id = ? AND client_id = ?", params)
    return get_chat(chat_id, client_id)


def delete_chat(chat_id: str, client_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE id = ? AND client_id = ?", (chat_id, client_id))


def add_message(
    chat_id: str,
    role: str,
    content: str,
    tool_events: list[dict] | None = None,
    attachments: list[dict] | None = None,
) -> Message:
    message_id = str(uuid4())
    timestamp = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO messages(id, chat_id, role, content, tool_events, attachments, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                chat_id,
                role,
                content,
                encode_json(tool_events),
                encode_json(attachments),
                timestamp,
            ),
        )
        conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (timestamp, chat_id))
    return Message(
        id=message_id,
        chat_id=chat_id,
        role=role,
        content=content,
        tool_events=tool_events or [],
        attachments=attachments or [],
        created_at=datetime.fromisoformat(timestamp),
    )


def replace_last_assistant_message(chat_id: str) -> None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id FROM messages
            WHERE chat_id = ? AND role = 'assistant'
            ORDER BY created_at DESC LIMIT 1
            """,
            (chat_id,),
        ).fetchone()
        if row:
            conn.execute("DELETE FROM messages WHERE id = ?", (row["id"],))
