"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

const components: Components = {
  h1: ({ children }) => (
    <h1 className="mb-3 mt-5 text-lg font-semibold text-navy first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-2 mt-4 border-b border-border pb-1 text-base font-semibold text-navy first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-3 text-sm font-semibold text-navy first:mt-0">
      {children}
    </h3>
  ),
  p: ({ children }) => (
    <p className="mb-3 leading-relaxed last:mb-0">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="mb-3 list-disc space-y-1.5 pl-5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-3 list-decimal space-y-1.5 pl-5">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => (
    <strong className="font-semibold text-navy">{children}</strong>
  ),
  em: ({ children }) => <em className="italic text-navy/90">{children}</em>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-navy underline decoration-gold/70 underline-offset-2 hover:text-gold"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-4 border-gold bg-off-white/80 py-2 pl-3 pr-2 text-sm italic text-navy/90">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-4 border-border" />,
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto rounded-lg border border-border">
      <table className="w-full min-w-full border-collapse text-xs">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-off-white text-left font-semibold">{children}</thead>
  ),
  th: ({ children }) => (
    <th className="border-b border-border px-3 py-2 text-navy">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border-b border-border/60 px-3 py-2 align-top">{children}</td>
  ),
  tr: ({ children }) => <tr className="last:border-0">{children}</tr>,
  pre: ({ children }) => <>{children}</>,
  code: ({ className, children, ...props }) => {
    const text = String(children ?? "").replace(/\n$/, "");
    const language = /language-([\w+#-]+)/i.exec(className || "")?.[1];
    const isBlock = Boolean(language) || text.includes("\n");

    if (!isBlock) {
      return (
        <code
          className="rounded-md bg-off-white px-1.5 py-0.5 font-mono text-[0.85em] text-navy ring-1 ring-border"
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <div className="my-3 overflow-hidden rounded-lg border border-border shadow-sm">
        {language && (
          <div className="flex items-center justify-between border-b border-gold/25 bg-navy px-3 py-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-gold">
              {language}
            </span>
          </div>
        )}
        <pre className="overflow-x-auto bg-[#0f1f3a] p-3 text-[13px] leading-relaxed">
          <code className="font-mono text-off-white">{text}</code>
        </pre>
      </div>
    );
  },
};

interface Props {
  content: string;
}

export function MarkdownContent({ content }: Props) {
  return (
    <div className="markdown-answer max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
