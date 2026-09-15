"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  onFileClick?: (filePath: string) => void;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = "",
  onFileClick,
}) => {
  if (!content) return null;

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ ...props }) => (
            <h1 className="text-lg font-bold text-white tracking-tight mt-5 mb-2.5 pb-1 border-b border-white/10" {...props} />
          ),
          h2: ({ ...props }) => (
            <h2 className="text-base font-semibold text-white tracking-tight mt-4 mb-2 pb-0.5 border-b border-white/5" {...props} />
          ),
          h3: ({ ...props }) => (
            <h3 className="text-sm font-semibold text-purple-300 mt-3.5 mb-1.5" {...props} />
          ),
          h4: ({ ...props }) => (
            <h4 className="text-xs font-semibold text-white/90 uppercase tracking-wider mt-3 mb-1" {...props} />
          ),
          p: ({ ...props }) => (
            <p className="text-xs sm:text-sm text-white/80 leading-relaxed mb-3" {...props} />
          ),
          ul: ({ ...props }) => (
            <ul className="list-disc list-outside pl-5 mb-3 space-y-1 text-xs sm:text-sm text-white/80" {...props} />
          ),
          ol: ({ ...props }) => (
            <ol className="list-decimal list-outside pl-5 mb-3 space-y-1 text-xs sm:text-sm text-white/80" {...props} />
          ),
          li: ({ ...props }) => (
            <li className="leading-relaxed pl-0.5" {...props} />
          ),
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-2 border-purple-500/50 pl-3.5 py-1 my-3 bg-purple-500/[0.04] rounded-r-lg text-xs sm:text-sm text-white/70 italic" {...props} />
          ),
          hr: () => (
            <hr className="border-white/10 my-4" />
          ),
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-4 rounded-xl border border-white/10 bg-black/30">
              <table className="w-full text-left text-xs text-white/80 border-collapse" {...props} />
            </div>
          ),
          thead: ({ ...props }) => (
            <thead className="bg-white/5 border-b border-white/10 text-white font-medium" {...props} />
          ),
          tbody: ({ ...props }) => (
            <tbody className="divide-y divide-white/5 font-mono text-[11px]" {...props} />
          ),
          tr: ({ ...props }) => (
            <tr className="hover:bg-white/[0.02] transition-colors" {...props} />
          ),
          th: ({ ...props }) => (
            <th className="px-3.5 py-2.5 font-semibold text-white/90" {...props} />
          ),
          td: ({ ...props }) => (
            <td className="px-3.5 py-2 text-white/75" {...props} />
          ),
          strong: ({ ...props }) => (
            <strong className="font-semibold text-white" {...props} />
          ),
          em: ({ ...props }) => (
            <em className="text-white/90 italic" {...props} />
          ),
          code: ({ inline, className: codeClassName, children, ...props }: any) => {
            const codeText = String(children).replace(/\n$/, "");
            const isPathLike = onFileClick && inline && typeof codeText === "string" && (codeText.includes("/") || codeText.endsWith(".py") || codeText.endsWith(".js") || codeText.endsWith(".ts") || codeText.endsWith(".json") || codeText.endsWith(".md"));

            if (inline) {
              if (isPathLike) {
                return (
                  <button
                    type="button"
                    onClick={() => onFileClick?.(codeText)}
                    className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded-md bg-purple-500/15 hover:bg-purple-500/30 text-purple-300 hover:text-purple-100 font-mono text-[11px] border border-purple-500/30 hover:border-purple-400 transition-colors cursor-pointer"
                    title={`Inspect ${codeText} in File Intelligence`}
                  >
                    {children}
                  </button>
                );
              }
              return (
                <code className="px-1.5 py-0.5 mx-0.5 rounded-md bg-white/10 text-purple-300 font-mono text-[11px] border border-white/5" {...props}>
                  {children}
                </code>
              );
            }

            return (
              <div className="relative my-3 rounded-xl overflow-hidden border border-white/10 bg-black/60">
                <pre className="p-3.5 overflow-x-auto text-xs font-mono text-emerald-300/90 leading-relaxed">
                  <code>{children}</code>
                </pre>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
