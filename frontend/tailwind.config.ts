import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#ffffff",
        foreground: "#0a0a0a",
        panel: "#ffffff",
        muted: "#f5f5f5",
        border: "#d4d4d4",
        accent: "#0a0a0a",
        accent2: "#404040",
        danger: "#0a0a0a",
      },
      boxShadow: {
        soft: "0 18px 48px rgba(0, 0, 0, 0.08)",
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "ui-sans-serif", "system-ui"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [typography],
} satisfies Config;
