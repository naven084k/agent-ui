import { Check, Copy } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { copyToClipboard } from "@/lib/utils";

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose max-w-none prose-sm prose-neutral prose-pre:bg-transparent prose-table:text-sm prose-headings:font-display prose-headings:font-bold prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-code:text-foreground prose-code:bg-muted prose-code:rounded prose-code:px-1 prose-code:py-0.5 prose-code:text-[0.85em] prose-code:before:content-none prose-code:after:content-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code(props) {
            const { children, className } = props;
            const match = /language-(\w+)/.exec(className || "");
            const value = String(children).replace(/\n$/, "");
            if (!match) {
              return (
                <code className="rounded bg-accent-dim border border-accent/10 px-1.5 py-0.5 text-accent/90 font-mono text-[0.85em]">
                  {value}
                </code>
              );
            }
            return <CodeBlock language={match[1]} value={value} />;
          },
          table(props) {
            return (
              <div className="overflow-x-auto rounded-xl border border-border">
                <table className="w-full">{props.children}</table>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function CodeBlock({ language, value }: { language: string; value: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-panel my-3">
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{language}</span>
        <button
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:text-foreground hover:bg-muted"
          onClick={async () => {
            await copyToClipboard(value);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1200);
          }}
          type="button"
        >
          {copied ? <Check className="h-3 w-3 text-accent" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={oneLight}
        customStyle={{ margin: 0, background: "transparent", padding: "1rem", fontSize: "0.8rem" }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}
