"use client";

import React from "react";
import { Brain, Sparkles, Trash2 } from "lucide-react";

interface NavbarProps {
  currentRepo: string | null;
  onClear: () => void;
  isClearing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentRepo, onClear, isClearing }) => {
  return (
    <header className="sticky top-0 z-50 w-full px-6 py-3 border-b border-white/10 bg-[#070a12]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#7c5cff] to-[#29d2f7] p-[1px] flex items-center justify-center shadow-lg shadow-purple-500/20">
            <div className="w-full h-full bg-[#0a0d1a] rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-purple-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-white/90 to-white/70 bg-clip-text text-transparent">
                RepoMind AI
              </span>
              <span className="px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                v0.1.0
              </span>
            </div>
            <p className="text-xs text-white/50 hidden sm:block">
              Repository Intelligence &bull; Architecture &bull; RAG Q&amp;A
            </p>
          </div>
        </div>

        {/* Status & Actions */}
        <div className="flex items-center gap-3">
          {currentRepo && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-white/60">Active:</span>
              <span className="font-mono text-white/90 font-medium">{currentRepo}</span>
            </div>
          )}

          {currentRepo && (
            <button
              onClick={onClear}
              disabled={isClearing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-rose-500/15 border border-white/10 hover:border-rose-500/30 text-white/70 hover:text-rose-400 text-xs transition-colors"
              title="Clear cached repository analysis"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{isClearing ? "Clearing..." : "Clear Session"}</span>
            </button>
          )}

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 hover:text-white transition-colors"
            title="GitHub"
          >
            <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </a>
        </div>
      </div>
    </header>
  );
};
