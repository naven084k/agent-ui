import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-[36px] w-full resize-none bg-transparent px-0 py-1 text-sm text-foreground outline-none placeholder:text-muted-foreground",
          className,
        )}
        {...props}
      />
    );
  },
);

Textarea.displayName = "Textarea";
