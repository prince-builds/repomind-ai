"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronRight, Layers, FileCode } from "lucide-react";
import { RetrievalHit } from "@/lib/types";

interface RetrievedContextProps {
  hits: RetrievalHit[];
  title?: string;
}

export const RetrievedContext: React.FC<RetrievedContextProps> = ({
  hits,
  title = "Retrieved Context (FAISS Chunks)",
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!hits || hits.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel mt-4 overflow-hidden border-white/10">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-white/[0.03] hover:bg-white/[0.06] text-left transition-colors"
      >
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-semibold text-white/90">{title}</span>
          <span className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 text-[10px] font-mono">
            {hits.length} chunks
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-white/50" />
        ) : (
          <ChevronRight className="w-4 h-4 text-white/50" />
        )}
      </button>

      {isExpanded && (
        <div className="p-4 space-y-3 bg-black/30 border-t border-white/5">
          {hits.map((hit, idx) => (
            <div
              key={`${hit.file_path}-${hit.chunk_index}-${idx}`}
              className="p-3 rounded-xl bg-white/[0.03] border border-white/5 space-y-2"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-1.5 font-mono text-purple-300">
                  <FileCode className="w-3.5 h-3.5 text-purple-400" />
                  <span>{hit.file_path}</span>
                  <span className="text-white/40">#chunk-{hit.chunk_index}</span>
                </div>
                <div className="px-2 py-0.5 rounded bg-white/5 text-white/60 text-[11px] font-mono">
                  Similarity: <span className="text-emerald-400 font-medium">{hit.score.toFixed(4)}</span>
                </div>
              </div>

              <pre className="p-2.5 rounded-lg bg-black/50 text-white/80 font-mono text-xs overflow-x-auto border border-white/5">
                <code>{hit.content}</code>
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
