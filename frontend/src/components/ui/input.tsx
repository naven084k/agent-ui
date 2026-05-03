import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-11 w-full rounded-xl border border-border bg-white px-4 text-sm text-foreground outline-none placeholder:text-neutral-400 focus:border-accent",
        className,
      )}
      {...props}
    />
  );
}
