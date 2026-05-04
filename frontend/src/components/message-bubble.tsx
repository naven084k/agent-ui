import { motion } from "framer-motion";

import { Markdown } from "@/components/markdown";
import type { Message } from "@/lib/types";

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40"
          style={{ animation: `dot-bounce 1.2s ease-in-out ${delay}ms infinite` }}
        />
      ))}
    </div>
  );
}

export function MessageBubble({ message, loading = false }: { message: Message; loading?: boolean }) {
  const isUser = message.role === "user";
  const showLoader = loading && !message.content.trim();

  if (isUser) {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex justify-end"
      >
        <div className="max-w-[65%] rounded-2xl rounded-br-sm bg-zinc-900 px-4 py-3 text-sm leading-relaxed text-white">
          {message.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex items-start"
    >
      <div className="min-w-0 flex-1">
        {showLoader ? (
          <TypingDots />
        ) : (
          <div className="text-sm leading-relaxed text-foreground">
            <Markdown content={message.content} />
          </div>
        )}
      </div>
    </motion.div>
  );
}
