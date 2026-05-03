import { SendHorizontal, Square } from "lucide-react";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
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
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }, [props.value]);

  return (
    <div className="border-t border-border bg-white px-1 pt-2">
      <div className="bg-white">
        {props.streaming && (
          <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-neutral-500">
            <span className="flex items-center gap-1.5" aria-hidden="true">
              <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500 [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500 [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500" />
            </span>
            <span>Generating response</span>
          </div>
        )}
        <Textarea
          ref={textareaRef}
          className="min-h-[32px] border-0 bg-transparent px-0 py-1 focus:border-0"
          placeholder="Message Nexora Agent..."
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              props.onSend();
            }
          }}
        />
        <div className="mt-1 flex flex-wrap items-center justify-end gap-2">
          <div className="flex items-center gap-2">
            {props.streaming && (
              <Button size="icon" variant="outline" onClick={props.onStop}>
                <Square className="h-4 w-4" />
              </Button>
            )}
            <Button disabled={props.disabled || !props.value.trim()} size="icon" onClick={props.onSend}>
              <SendHorizontal className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
