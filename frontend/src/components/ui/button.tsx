import * as React from "react";
import { Slot } from "@radix-ui/react-slot";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "default" | "ghost" | "outline" | "accent" | "danger";
  size?: "sm" | "md" | "icon";
};

export function Button({
  className,
  asChild,
  variant = "default",
  size = "md",
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40",
        variant === "default" && "bg-muted text-foreground border border-border-strong hover:border-accent/30 hover:bg-muted/80",
        variant === "ghost" && "bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted",
        variant === "outline" && "border border-border-strong bg-transparent text-foreground hover:border-accent/40 hover:bg-accent-dim",
        variant === "accent" && "bg-accent text-background font-semibold hover:bg-accent/90 shadow-glow-sm",
        variant === "danger" && "bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20",
        size === "sm" && "h-8 px-3 text-sm gap-1.5",
        size === "md" && "h-10 px-4 text-sm gap-2",
        size === "icon" && "h-9 w-9",
        className,
      )}
      {...props}
    />
  );
}
