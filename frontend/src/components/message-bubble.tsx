import { motion } from "framer-motion";
import { ChevronDown, Wrench } from "lucide-react";
import { useState } from "react";

import { Markdown } from "@/components/markdown";
import type { Message } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function MessageBubble({ message, loading = false }: { message: Message; loading?: boolean }) {
  const [open, setOpen] = useState(false);
  const isUser = message.role === "user";
  const showLoader = loading && !message.content.trim();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className="max-w-[85%] px-1 py-1">
        <div className="mb-2 flex items-center justify-between gap-4 text-[11px] uppercase tracking-[0.22em] text-neutral-500">
          <span>{isUser ? "You" : "Assistant"}</span>
          <span>{formatDate(message.created_at)}</span>
        </div>
        {showLoader ? (
          <div className="inline-flex items-center gap-3 rounded-2xl border border-border bg-neutral-50 px-4 py-3 text-sm text-neutral-600">
            <span>Thinking</span>
            <span className="flex items-center gap-1" aria-hidden="true">
              <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500 [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500 [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500" />
            </span>
          </div>
        ) : (
          <Markdown content={message.content} />
        )}
        {!!message.tool_events.length && (
          <div className="mt-4 rounded-2xl border border-border bg-neutral-50">
            <button
              className="flex w-full items-center justify-between px-4 py-3 text-sm"
              onClick={() => setOpen((value) => !value)}
              type="button"
            >
              <span className="inline-flex items-center gap-2">
                <Wrench className="h-4 w-4 text-black" />
                Tool activity
              </span>
              <ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
            </button>
            {open && (
              <div className="space-y-3 border-t border-border px-4 py-4">
                {message.tool_events.map((event) => (
                  <div key={event.id} className="rounded-xl border border-border bg-white p-3 text-sm">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-medium">{event.name}</span>
                      <span className="text-xs uppercase tracking-[0.2em] text-neutral-500">{event.status}</span>
                    </div>
                    <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-neutral-700">
                      {JSON.stringify(event.input, null, 2)}
                    </pre>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-neutral-500">{event.output}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
