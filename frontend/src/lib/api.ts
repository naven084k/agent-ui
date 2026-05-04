import type { ChatDetail, ChatSummary, ModelInfo } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getClientId(): string {
  const KEY = "nexora_client_id";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

function baseHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Client-ID": getClientId(),
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...baseHeaders(),
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  listChats(search = "") {
    return request<ChatSummary[]>(`/api/chats?search=${encodeURIComponent(search)}`);
  },
  createChat(payload: { title: string; model: string; system_prompt?: string }) {
    return request<ChatDetail>("/api/chats", { method: "POST", body: JSON.stringify(payload) });
  },
  getChat(chatId: string) {
    return request<ChatDetail>(`/api/chats/${chatId}`);
  },
  updateChat(chatId: string, payload: Record<string, unknown>) {
    return request<ChatDetail>(`/api/chats/${chatId}`, { method: "PATCH", body: JSON.stringify(payload) });
  },
  deleteChat(chatId: string) {
    return request<{ ok: true }>(`/api/chats/${chatId}`, { method: "DELETE" });
  },
  regenerate(chatId: string) {
    return request<ChatDetail>(`/api/chats/${chatId}/regenerate`, { method: "POST" });
  },
  getModels() {
    return request<ModelInfo[]>("/api/models");
  },
  async streamChat(payload: Record<string, unknown>, onEvent: (event: any) => void, signal?: AbortSignal) {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: "POST",
      headers: baseHeaders(),
      body: JSON.stringify(payload),
      signal,
    });
    if (!response.ok || !response.body) {
      throw new Error(await response.text());
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n");
      buffer = parts.pop() ?? "";
      for (const line of parts) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);
        if (event.type === "error") throw new Error(event.data);
        onEvent(event);
      }
    }
  },
};
