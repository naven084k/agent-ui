import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-[44px] w-full resize-none rounded-2xl border border-border bg-white px-4 py-2.5 text-sm text-foreground outline-none placeholder:text-neutral-400 focus:border-accent",
          className,
        )}
        {...props}
      />
    );
  },
);

Textarea.displayName = "Textarea";
