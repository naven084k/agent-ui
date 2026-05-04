import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Plus, Trash2 } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import type { ChatSummary } from "@/lib/types";

type Props = {
  chats: ChatSummary[];
  currentChatId?: string;
  search: string;
  onSearch: (value: string) => void;
  onCreate: () => void;
  onSelect: (chatId: string) => void;
  onDelete: (chatId: string) => void;
  onRename: (chatId: string) => void;
  onPin: (chat: ChatSummary) => void;
};

export function ChatSidebar(props: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-sidebar">
      {/* Brand */}
      <div className="flex h-14 shrink-0 items-center border-b border-border px-5">
        <span className="font-display text-lg font-bold tracking-tight text-foreground">Nexora</span>
      </div>

      {/* New conversation */}
      <div className="shrink-0 p-3">
        <button
          onClick={props.onCreate}
          type="button"
          className="flex w-full items-center gap-2 rounded-lg border border-dashed border-border-strong px-3 py-2.5 text-sm font-medium text-muted-foreground transition-all hover:border-accent/40 hover:bg-white hover:text-accent"
        >
          <Plus className="h-4 w-4 shrink-0" />
          New conversation
        </button>
      </div>

      {/* Section label */}
      {props.chats.length > 0 && (
        <div className="shrink-0 px-4 pb-2 pt-1">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/40">
            Recent
          </p>
        </div>
      )}

      {/* Chat list */}
      <div className="scrollbar-thin flex-1 overflow-y-auto px-3 pb-4">
        <AnimatePresence initial={false}>
          {props.chats.map((chat) => {
            const isActive = props.currentChatId === chat.id;
            const isHovered = hoveredId === chat.id;
            return (
              <motion.div
                key={chat.id}
                layout
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.15 }}
                onMouseEnter={() => setHoveredId(chat.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`relative mb-1 min-w-0 rounded-xl transition-all ${
                  isActive
                    ? "bg-white shadow-card border border-border"
                    : "hover:bg-white/80 border border-transparent"
                }`}
              >
                {/* Active accent bar */}
                {isActive && (
                  <div className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full bg-accent" />
                )}

                <div className="flex w-full items-start px-3 py-2.5">
                  <button
                    type="button"
                    onClick={() => props.onSelect(chat.id)}
                    className="min-w-0 flex-1 text-left"
                  >
                    {/* Title row */}
                    <div className="flex items-center justify-between gap-2">
                      <span className={`truncate text-[13px] font-semibold leading-snug ${isActive ? "text-foreground" : "text-foreground/70"}`}>
                        {chat.title}
                      </span>
                      {!isHovered && (
                        <span className="shrink-0 text-[10px] text-muted-foreground/50">
                          {timeAgo(chat.updated_at)}
                        </span>
                      )}
                    </div>

                    {/* Preview */}
                    <p className="mt-1 truncate text-[12px] leading-relaxed text-muted-foreground/60">
                      {chat.last_message || "No messages yet"}
                    </p>
                  </button>

                  {/* Delete — visible on hover */}
                  {isHovered && (
                    <button
                      type="button"
                      title="Delete"
                      onClick={(e) => { e.stopPropagation(); props.onDelete(chat.id); }}
                      className="ml-1 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-red-100 hover:text-red-500"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {props.chats.length === 0 && (
          <p className="px-2 py-8 text-center text-xs text-muted-foreground">
            No conversations yet
          </p>
        )}
      </div>
    </aside>
  );
}
