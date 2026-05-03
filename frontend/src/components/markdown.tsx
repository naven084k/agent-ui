import { Check, Copy } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { copyToClipboard } from "@/lib/utils";

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose max-w-none prose-neutral prose-pre:bg-transparent prose-table:text-sm">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code(props) {
            const { children, className } = props;
            const match = /language-(\w+)/.exec(className || "");
            const value = String(children).replace(/\n$/, "");
            if (!match) {
              return <code className="rounded bg-black/[0.05] px-1.5 py-0.5 text-[0.9em]">{value}</code>;
            }
            return <CodeBlock language={match[1]} value={value} />;
          },
          table(props) {
            return <table className="w-full overflow-hidden rounded-xl border border-border">{props.children}</table>;
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
    <div className="overflow-hidden rounded-2xl border border-border bg-neutral-50">
      <div className="flex items-center justify-between border-b border-border px-4 py-2 text-xs uppercase tracking-[0.2em] text-neutral-500">
        <span>{language}</span>
        <button
          className="inline-flex items-center gap-1 rounded-lg px-2 py-1 hover:bg-black/5"
          onClick={async () => {
            await copyToClipboard(value);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1200);
          }}
          type="button"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter language={language} style={oneDark} customStyle={{ margin: 0, background: "transparent" }}>
        {value}
      </SyntaxHighlighter>
    </div>
  );
}
