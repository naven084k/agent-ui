import { AnimatePresence, motion } from "framer-motion";
import { MessageSquarePlus, Pin, Search, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
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
  return (
    <aside className="flex h-full w-[320px] flex-col border-r border-border bg-white p-4">
      <Button className="mb-4 w-full justify-start gap-2" onClick={props.onCreate}>
        <MessageSquarePlus className="h-4 w-4" />
        New Chat
      </Button>
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
        <Input className="pl-10" placeholder="Search chats" value={props.search} onChange={(e) => props.onSearch(e.target.value)} />
      </div>
      <div className="scrollbar-thin flex-1 space-y-2 overflow-y-auto pr-1">
        <AnimatePresence initial={false}>
          {props.chats.map((chat) => (
            <motion.button
              layout
              key={chat.id}
              type="button"
              onClick={() => props.onSelect(chat.id)}
              className={`w-full rounded-2xl border p-3 text-left transition ${
                props.currentChatId === chat.id
                  ? "border-black bg-black/[0.03]"
                  : "border-transparent bg-white hover:border-border hover:bg-black/[0.02]"
              }`}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <div>
                  <div className="line-clamp-1 text-sm font-medium">{chat.title}</div>
                  <div className="text-xs text-neutral-500">{formatDate(chat.updated_at)}</div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    className="rounded-lg p-2 hover:bg-white/10"
                    onClick={(e) => {
                      e.stopPropagation();
                      props.onPin(chat);
                    }}
                    type="button"
                  >
                    <Pin className={`h-3.5 w-3.5 ${chat.pinned ? "fill-current text-black" : "text-neutral-400"}`} />
                  </button>
                  <button
                    className="rounded-lg p-2 hover:bg-white/10"
                    onClick={(e) => {
                      e.stopPropagation();
                      props.onRename(chat.id);
                    }}
                    type="button"
                  >
                    <span className="text-xs text-neutral-400">Aa</span>
                  </button>
                  <button
                    className="rounded-lg p-2 hover:bg-white/10"
                    onClick={(e) => {
                      e.stopPropagation();
                      props.onDelete(chat.id);
                    }}
                    type="button"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-neutral-400" />
                  </button>
                </div>
              </div>
              <div className="line-clamp-2 text-xs text-neutral-500">{chat.last_message || "No messages yet"}</div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </aside>
  );
}
