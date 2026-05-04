import { AnimatePresence, motion } from "framer-motion";
import { RefreshCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { ChatSidebar } from "@/components/chat-sidebar";
import { Composer } from "@/components/composer";
import { MessageBubble } from "@/components/message-bubble";
import { api } from "@/lib/api";
import type { ChatDetail, ChatSummary, Message, ModelInfo, ToolEvent } from "@/lib/types";

const DEFAULT_MODEL = import.meta.env.VITE_DEFAULT_MODEL ?? "gpt-4o-mini";

const SUGGESTIONS = [
  "What's the weather in New York right now?",
  "What is Apple's current stock price?",
  "Convert 1000 USD to EUR",
  "Air quality in Delhi today",
];

const EMPTY_TITLE = "How can I help?";
const EMPTY_SUBTITLE = "Ask me anything. I can answer questions, look things up, and help you get things done.";

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
  const isEmpty = activeMessages.length === 0;

  useEffect(() => { void bootstrap(); }, []);
  useEffect(() => { void loadChats(search); }, [search]);
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
    setChats(loadedChats);
    setModels(loadedModels);
    setSelectedModel(loadedModels[0]?.name || DEFAULT_MODEL);
    if (loadedChats[0]) {
      const detail = await api.getChat(loadedChats[0].id);
      setActiveChat(detail);
      setSelectedModel(detail.model || loadedModels[0]?.name || DEFAULT_MODEL);
    } else {
      const model = loadedModels[0]?.name || DEFAULT_MODEL;
      const chat = await api.createChat({ title: "New chat", model });
      setActiveChat(chat);
      setChats([chat]);
      setSelectedModel(model);
    }
  }

  async function loadChats(query: string) {
    setChats(await api.listChats(query));
  }

  async function selectChat(chatId: string) {
    const detail = await api.getChat(chatId);
    setActiveChat(detail);
    setSelectedModel(detail.model || DEFAULT_MODEL);
  }

  async function createChat() {
    const model = selectedModel || models[0]?.name || DEFAULT_MODEL;
    const chat = await api.createChat({ title: "New chat", model });
    setActiveChat(chat);
    setChats((prev) => [chat, ...prev]);
    setSelectedModel(model);
    return chat;
  }

  async function sendMessage(contentOverride?: string, chatOverride?: ChatDetail) {
    let sourceChat = chatOverride ?? activeChat;
    const content = contentOverride ?? composer;
    if (!content.trim() || streaming) return;
    if (!sourceChat) sourceChat = await createChat();

    const model = resolveModel(sourceChat);
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

    setActiveChat({ ...sourceChat, model, messages: [...sourceChat.messages, nextMessage, placeholder] });
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
          messages: [...sourceChat.messages, nextMessage].map((m) => ({
            role: m.role,
            content: m.content,
            attachments: [],
          })),
          use_tools: true,
        },
        (event) => {
          setActiveChat((current) => {
            if (!current) return current;
            const messages = [...current.messages];
            const last = messages[messages.length - 1];
            if (!last) return current;
            if (event.type === "token") last.content += event.data;
            if (event.type === "tool_start") {
              toolEvents.push({ ...event.data, status: "running", output: "" });
              last.tool_events = [...toolEvents];
            }
            if (event.type === "tool_end") {
              const i = toolEvents.findIndex((t) => t.id === event.data.id);
              if (i >= 0) toolEvents[i] = event.data;
              last.tool_events = [...toolEvents];
            }
            return { ...current, messages };
          });
        },
        controller.signal,
      );
      await Promise.all([loadChats(search), selectChat(sourceChat.id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      abortRef.current = null;
      setStreaming(false);
    }
  }

  async function stopStreaming() {
    abortRef.current?.abort();
    setStreaming(false);
  }

  async function regenerateResponse() {
    if (!activeChat || streaming) return;
    const refreshed = await api.regenerate(activeChat.id);
    const lastUser = [...refreshed.messages].reverse().find((m) => m.role === "user");
    if (!lastUser) { setActiveChat(refreshed); return; }
    await sendMessage(lastUser.content, refreshed);
  }

  const headerTitle = useMemo(() => activeChat?.title || "New conversation", [activeChat?.title]);
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
        onSelect={(id) => void selectChat(id)}
        onDelete={async (id) => {
          await api.deleteChat(id);
          const refreshed = await api.listChats(search);
          setChats(refreshed);
          if (activeChat?.id === id) setActiveChat(null);
        }}
        onRename={async (id) => {
          const title = window.prompt("Rename conversation");
          if (!title) return;
          await api.updateChat(id, { title });
          await loadChats(search);
          if (activeChat?.id === id) await selectChat(id);
        }}
        onPin={async (chat) => {
          await api.updateChat(chat.id, { pinned: !chat.pinned });
          await loadChats(search);
        }}
      />

      <main className="flex min-w-0 flex-1 flex-col bg-white">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-6">
          <span className="text-sm font-medium text-foreground/50 truncate max-w-xs">
            {headerTitle}
          </span>
          <div className="flex items-center gap-2">
            {!!activeMessages.length && !streaming && (
              <button
                onClick={() => void regenerateResponse()}
                type="button"
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <RefreshCcw className="h-3.5 w-3.5" />
                Retry
              </button>
            )}
            <span className="rounded-md border border-border bg-muted px-2.5 py-1 font-mono text-[11px] text-muted-foreground">
              {resolveModel(activeChat)}
            </span>
          </div>
        </header>

        {/* Scrollable message area */}
        <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto">
          {isEmpty ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="flex h-full flex-col items-center justify-center px-6 py-16"
            >
              <h2 className="font-display text-[28px] font-bold text-foreground">
                {EMPTY_TITLE}
              </h2>
              <p className="mt-2 max-w-[340px] text-center text-[15px] leading-relaxed text-muted-foreground">
                {EMPTY_SUBTITLE}
              </p>

              <div className="mt-10 grid w-full max-w-xl grid-cols-2 gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => { setComposer(s); }}
                    className="group rounded-xl border border-border bg-white px-4 py-3.5 text-left text-[13px] font-medium text-foreground/60 shadow-panel transition-all hover:border-accent/30 hover:text-foreground hover:shadow-soft"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </motion.div>
          ) : (
            <div className="mx-auto w-full max-w-chat px-6 py-8">
              <AnimatePresence initial={false}>
                <div className="space-y-8">
                  {activeMessages.map((message) => (
                    <MessageBubble
                      key={message.id}
                      message={message}
                      loading={message.id === loadingMessageId}
                    />
                  ))}
                </div>
              </AnimatePresence>
              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="shrink-0 border-t border-border bg-white px-4 pb-5 pt-3">
          <div className="mx-auto w-full max-w-chat">
            {error && (
              <div className="mb-3 flex items-start gap-2 rounded-xl border border-danger/20 bg-danger/5 px-4 py-2.5">
                <span className="text-sm text-danger/90">{error}</span>
              </div>
            )}
            <Composer
              value={composer}
              onChange={setComposer}
              onSend={() => void sendMessage()}
              onStop={() => void stopStreaming()}
              streaming={streaming}
            />
            <p className="mt-2.5 text-center text-[11px] text-muted-foreground/50">
              <kbd className="rounded border border-border/80 px-1 py-0.5 font-mono text-[10px]">Enter</kbd> to send
              {" · "}
              <kbd className="rounded border border-border/80 px-1 py-0.5 font-mono text-[10px]">Shift+Enter</kbd> for newline
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
