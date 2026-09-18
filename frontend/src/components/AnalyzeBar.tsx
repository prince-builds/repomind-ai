"use client";

import React, { useState } from "react";
import { Search, Loader2, Sparkles, ArrowRight } from "lucide-react";

interface AnalyzeBarProps {
  onAnalyze: (url: string) => void;
  isLoading: boolean;
  activeUrl: string;
}

const PRESET_REPOS = [
  { label: "AI Study Copilot", url: "https://github.com/prince-builds/ai-study-copilot" },
  { label: "NexusAI RAG", url: "https://github.com/prince-builds/nexusai-rag-chatbot" },
  { label: "FastAPI", url: "https://github.com/fastapi/fastapi" },
  { label: "Hello World", url: "https://github.com/octocat/Hello-World" },
];

export const AnalyzeBar: React.FC<AnalyzeBarProps> = ({ onAnalyze, isLoading, activeUrl }) => {
  const [inputUrl, setInputUrl] = useState(activeUrl || "");
  const [prevActiveUrl, setPrevActiveUrl] = useState(activeUrl);

  if (activeUrl !== prevActiveUrl) {
    setPrevActiveUrl(activeUrl);
    setInputUrl(activeUrl || "");
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUrl.trim()) {
      onAnalyze(inputUrl.trim());
    }
  };

  return (
    <div className="w-full">
      {/* Hero Header */}
      <div className="text-center max-w-2xl mx-auto mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-medium mb-3">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Universal Codebase Understanding Engine</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
          Inspect, Map &amp; Query Any Repository
        </h1>
        <p className="text-sm text-white/60">
          Clones, scans AST dependencies, builds local FAISS semantic indexes, and generates AI architecture blueprints.
        </p>
      </div>

      {/* Input Card */}
      <div className="glass-panel p-3 sm:p-4 max-w-3xl mx-auto mb-4">
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-2">
          <div className="relative w-full flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              disabled={isLoading}
              className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-sm text-white placeholder-white/40 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !inputUrl.trim()}
            className="w-full sm:w-auto btn-primary px-5 py-2.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 whitespace-nowrap"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Indexing Codebase...</span>
              </>
            ) : (
              <>
                <span>Analyze Repository</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Quick Presets */}
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-white/5">
          <span className="text-xs text-white/40 font-medium">Quick Presets:</span>
          {PRESET_REPOS.map((preset) => (
            <button
              key={preset.url}
              type="button"
              onClick={() => {
                setInputUrl(preset.url);
              }}
              disabled={isLoading}
              className="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/5 hover:border-white/10 transition-colors"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
