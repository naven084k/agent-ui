import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-9 w-full rounded-lg border border-border bg-muted px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground transition-colors focus:border-accent/40 focus:bg-muted/80",
        className,
      )}
      {...props}
    />
  );
}
