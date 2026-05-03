import * as React from "react";
import { Slot } from "@radix-ui/react-slot";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "default" | "ghost" | "outline" | "danger";
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
        "inline-flex items-center justify-center rounded-xl font-medium transition duration-200 disabled:cursor-not-allowed disabled:opacity-50",
        variant === "default" && "bg-black text-white hover:bg-neutral-800",
        variant === "ghost" && "bg-transparent text-foreground hover:bg-black/5",
        variant === "outline" && "border border-border bg-white hover:bg-black/5",
        variant === "danger" && "bg-black text-white hover:bg-neutral-800",
        size === "sm" && "h-9 px-3 text-sm",
        size === "md" && "h-11 px-4 text-sm",
        size === "icon" && "h-10 w-10",
        className,
      )}
      {...props}
    />
  );
}
