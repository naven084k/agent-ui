import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef } from "react";

import { Textarea } from "@/components/ui/textarea";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  disabled?: boolean;
  streaming?: boolean;
};

export function Composer(props: Props) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [props.value]);

  const hasText = !!props.value.trim();

  return (
    <div className="rounded-2xl border border-border bg-white shadow-soft transition-colors focus-within:border-accent/40 focus-within:shadow-glow">
      {props.streaming && (
        <div className="flex items-center gap-2 border-b border-border px-4 py-2">
          <div className="flex items-center gap-1">
            {[0, 150, 300].map((d) => (
              <span
                key={d}
                className="h-1.5 w-1.5 rounded-full bg-accent"
                style={{ animation: `dot-bounce 1.2s ease-in-out ${d}ms infinite` }}
              />
            ))}
          </div>
          <span className="text-xs font-medium text-accent/80">Generating response…</span>
        </div>
      )}

      <div className="flex items-end gap-3 px-4 py-3">
        <Textarea
          ref={textareaRef}
          className="flex-1 text-[15px] leading-relaxed"
          placeholder="Ask about the weather anywhere…"
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (!props.streaming && hasText) props.onSend();
            }
          }}
        />

        <div className="shrink-0 pb-0.5">
          {props.streaming ? (
            <button
              onClick={props.onStop}
              type="button"
              title="Stop"
              className="flex h-10 w-10 items-center justify-center rounded-full border border-border-strong bg-muted text-muted-foreground transition-all hover:border-danger/40 hover:bg-danger/10 hover:text-danger"
            >
              <Square className="h-4 w-4 fill-current" />
            </button>
          ) : (
            <button
              onClick={() => { if (hasText) props.onSend(); }}
              type="button"
              title="Send"
              className={`flex h-10 w-10 items-center justify-center rounded-full transition-all ${
                hasText
                  ? "bg-accent text-white shadow-glow-sm hover:bg-accent/90 active:scale-95 cursor-pointer"
                  : "bg-muted border border-border-strong text-muted-foreground/40 cursor-not-allowed"
              }`}
            >
              <ArrowUp className="h-5 w-5" strokeWidth={2.5} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
