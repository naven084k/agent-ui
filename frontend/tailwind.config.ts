import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#ffffff",
        foreground: "#18181b",
        sidebar: "#f4f4f5",
        panel: "#ffffff",
        muted: "#f4f4f5",
        "muted-foreground": "#71717a",
        border: "#e4e4e7",
        "border-strong": "#d4d4d8",
        accent: "#0369a1",
        "accent-dim": "rgba(3, 105, 161, 0.06)",
        "accent-glow": "rgba(3, 105, 161, 0.12)",
        danger: "#ef4444",
      },
      fontFamily: {
        sans: ["'DM Sans'", "ui-sans-serif", "system-ui"],
        display: ["'Syne'", "ui-sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 3px rgba(3, 105, 161, 0.12)",
        "glow-sm": "0 1px 3px rgba(3, 105, 161, 0.2), 0 0 0 1px rgba(3, 105, 161, 0.1)",
        soft: "0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04)",
        panel: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        card: "0 0 0 1px rgba(0,0,0,0.05), 0 2px 8px rgba(0,0,0,0.06)",
      },
      maxWidth: {
        chat: "680px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "dot-bounce": {
          "0%, 80%, 100%": { transform: "translateY(0)", opacity: "0.4" },
          "40%": { transform: "translateY(-4px)", opacity: "1" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.25s ease-out forwards",
        "dot-bounce": "dot-bounce 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [typography],
} satisfies Config;
