import { AnimatePresence, motion } from "framer-motion";
import { RefreshCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { ChatSidebar } from "@/components/chat-sidebar";
import { Composer } from "@/components/composer";
import { MessageBubble } from "@/components/message-bubble";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ChatDetail, ChatSummary, Message, ModelInfo, ToolEvent } from "@/lib/types";

const DEFAULT_MODEL = import.meta.env.VITE_DEFAULT_MODEL ?? "gpt-5.4-mini";

export default function App() {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChat, setActiveChat] = useState<ChatDetail | null>(null);
  const [search, setSearch] = useState("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [composer, setComposer] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string>("");
  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const activeMessages = activeChat?.messages ?? [];

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    void loadChats(search);
  }, [search]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeMessages]);

  function resolveModel(chat?: ChatDetail | null) {
    return chat?.model || selectedModel || DEFAULT_MODEL;
  }

  async function bootstrap() {
    const [loadedChats, loadedModels] = await Promise.all([
      api.listChats(),
      api.getModels().catch(() => []),
    ]);
    console.log("[bootstrap] chats", loadedChats.length, "models", loadedModels.map((model) => model.name));
    setChats(loadedChats);
    setModels(loadedModels);
    setSelectedModel(loadedModels[0]?.name || DEFAULT_MODEL);
    if (loadedChats[0]) {
      const detail = await api.getChat(loadedChats[0].id);
      setActiveChat(detail);
      setSelectedModel(detail.model || loadedModels[0]?.name || DEFAULT_MODEL);
    } else {
      const model = loadedModels[0]?.name || DEFAULT_MODEL;
      const chat = await api.createChat({
        title: "New chat",
        model,
      });
      setActiveChat(chat);
      setChats([chat]);
      setSelectedModel(model);
    }
  }

  async function loadChats(query: string) {
    const loaded = await api.listChats(query);
    console.log("[loadChats] query", query, "count", loaded.length);
    setChats(loaded);
  }

  async function selectChat(chatId: string) {
    const detail = await api.getChat(chatId);
    console.log("[selectChat] chat", chatId, "model", detail.model);
    setActiveChat(detail);
    setSelectedModel(detail.model || DEFAULT_MODEL);
  }

  async function createChat() {
    const model = selectedModel || models[0]?.name || DEFAULT_MODEL;
    console.log("[createChat] creating chat with model", model);
    const chat = await api.createChat({
      title: "New chat",
      model,
    });
    setActiveChat(chat);
    setChats((current) => [chat, ...current]);
    setSelectedModel(model);
    return chat;
  }

  async function sendMessage(contentOverride?: string, chatOverride?: ChatDetail) {
    let sourceChat = chatOverride ?? activeChat;
    const content = contentOverride ?? composer;
    if (!content.trim() || streaming) return;
    if (!sourceChat) {
      console.log("[sendMessage] no active chat; creating one first");
      sourceChat = await createChat();
    }
    const model = resolveModel(sourceChat);
    console.log("[sendMessage] chat", sourceChat.id, "model", model, "contentLength", content.length);
    setError("");
    setStreaming(true);

    const nextMessage: Message = {
      id: crypto.randomUUID(),
      chat_id: sourceChat.id,
      role: "user",
      content,
      tool_events: [],
      attachments: [],
      created_at: new Date().toISOString(),
    };
    const placeholder: Message = {
      id: crypto.randomUUID(),
      chat_id: sourceChat.id,
      role: "assistant",
      content: "",
      tool_events: [],
      attachments: [],
      created_at: new Date().toISOString(),
    };

    const updatedChat = { ...sourceChat, model, messages: [...sourceChat.messages, nextMessage, placeholder] };
    setActiveChat(updatedChat);
    setComposer("");

    const controller = new AbortController();
    abortRef.current = controller;
    const toolEvents: ToolEvent[] = [];

    try {
      await api.streamChat(
        {
          chat_id: sourceChat.id,
          model,
          system_prompt: sourceChat.system_prompt || "",
          messages: [...sourceChat.messages, nextMessage].map((message) => ({
            role: message.role,
            content: message.content,
            attachments: [],
          })),
          use_tools: true,
        },
        (event) => {
          if (event.type !== "token") {
            console.log("[stream event]", event.type, event.data);
          }
          setActiveChat((current) => {
            if (!current) return current;
            const messages = [...current.messages];
            const assistant = messages[messages.length - 1];
            if (!assistant) return current;
            if (event.type === "token") {
              assistant.content += event.data;
            }
            if (event.type === "tool_start") {
              toolEvents.push({ ...event.data, status: "running", output: "" });
              assistant.tool_events = [...toolEvents];
            }
            if (event.type === "tool_end") {
              const index = toolEvents.findIndex((item) => item.id === event.data.id);
              if (index >= 0) toolEvents[index] = event.data;
              assistant.tool_events = [...toolEvents];
            }
            return { ...current, messages };
          });
        },
        controller.signal,
      );
      await Promise.all([loadChats(search), selectChat(sourceChat.id)]);
    } catch (streamError) {
      console.error("[sendMessage] stream failed", streamError);
      setError(streamError instanceof Error ? streamError.message : "Streaming failed");
    } finally {
      abortRef.current = null;
      setStreaming(false);
    }
  }

  async function stopStreaming() {
    console.log("[stopStreaming] abort requested");
    abortRef.current?.abort();
    setStreaming(false);
  }

  async function regenerateResponse() {
    if (!activeChat || streaming) return;
    console.log("[regenerate] chat", activeChat.id);
    const refreshed = await api.regenerate(activeChat.id);
    const userMessages = refreshed.messages.filter((message) => message.role === "user");
    const lastUser = userMessages[userMessages.length - 1];
    if (!lastUser) {
      console.warn("[regenerate] no last user message found");
      setActiveChat(refreshed);
      return;
    }
    await sendMessage(lastUser.content, refreshed);
  }

  const headerTitle = useMemo(() => activeChat?.title || "Nexora Agent", [activeChat?.title]);
  const lastMessage = activeMessages[activeMessages.length - 1];
  const loadingMessageId = streaming && lastMessage?.role === "assistant" ? lastMessage.id : undefined;

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <ChatSidebar
        chats={chats}
        currentChatId={activeChat?.id}
        search={search}
        onSearch={setSearch}
        onCreate={() => void createChat()}
        onSelect={(chatId) => void selectChat(chatId)}
        onDelete={async (chatId) => {
          await api.deleteChat(chatId);
          const refreshed = await api.listChats(search);
          setChats(refreshed);
          if (activeChat?.id === chatId) {
            setActiveChat(null);
          }
        }}
        onRename={async (chatId) => {
          const title = window.prompt("Rename chat");
          if (!title) return;
          await api.updateChat(chatId, { title });
          await loadChats(search);
          if (activeChat?.id === chatId) await selectChat(chatId);
        }}
        onPin={async (chat) => {
          await api.updateChat(chat.id, { pinned: !chat.pinned });
          await loadChats(search);
        }}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h1 className="text-2xl font-semibold">{headerTitle}</h1>
          </div>
          <div className="flex items-center gap-2">
          </div>
        </header>

        <section className="flex min-h-0 flex-1 flex-col px-6">
          <div className="scrollbar-thin min-h-0 flex-1 space-y-4 overflow-y-auto py-6">
            <AnimatePresence initial={false}>
                {activeMessages.map((message) => (
                  <MessageBubble key={message.id} message={message} loading={message.id === loadingMessageId} />
                ))}
            </AnimatePresence>
            {!activeMessages.length && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex h-full items-center justify-center">
                <div className="max-w-xl rounded-[32px] border border-border bg-panel p-8 text-center shadow-soft">
                  <h2 className="mb-3 text-3xl font-semibold">Nexora Agent</h2>
                  <p className="text-neutral-500">A minimal AI workspace powered by OpenAI.</p>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && <div className="mb-3 rounded-2xl border border-black/20 bg-black/5 px-4 py-3 text-sm text-black">{error}</div>}

          <div className="sticky bottom-0 pb-6 pt-4">
            <div className="mb-2 flex justify-end gap-2 px-1">
              <Button
                size="sm"
                variant="outline"
                onClick={() => void regenerateResponse()}
              >
                <RefreshCcw className="mr-2 h-4 w-4" />
                Regenerate
              </Button>
              {!!activeChat?.messages.length && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const lastUser = [...(activeChat?.messages ?? [])].reverse().find((message) => message.role === "user");
                    if (lastUser) setComposer(lastUser.content);
                  }}
                >
                  Edit last
                </Button>
              )}
            </div>
            <Composer
              value={composer}
              onChange={setComposer}
              onSend={() => void sendMessage()}
              onStop={() => void stopStreaming()}
              streaming={streaming}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
