"use client";

import React, { useState } from "react";
import { MessageSquare, Send, Sparkles, Loader2, FileCode, Sliders, HelpCircle } from "lucide-react";
import { QAResponse } from "@/lib/types";
import { api } from "@/lib/api";
import { RetrievedContext } from "./RetrievedContext";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";

interface QATabProps {
  repoId: string;
  repoName: string;
  onSelectFile?: (filePath: string) => void;
}

const SAMPLE_QUESTIONS = [
  "What is the main architecture and data flow of this codebase?",
  "How are errors and exceptions handled across modules?",
  "What external dependencies and APIs are integrated?",
  "Where are the entry points and CLI/web routing defined?",
];

export const QATab: React.FC<QATabProps> = ({ repoId, repoName, onSelectFile }) => {
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await api.askQuestion(repoId, q, topK);
      setResponse(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Q&A query failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Query Form */}
      <div className="glass-panel p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-purple-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">Ask About {repoName}</h3>
          </div>
          <span className="text-xs text-white/40">FAISS Semantic Search + Groq RAG</span>
        </div>

        {/* Input Box */}
        <div className="space-y-3">
          <div className="relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How does the indexing and retrieval pipeline work?"
              className="w-full p-3.5 bg-black/40 border border-white/10 rounded-xl text-sm text-white placeholder-white/40 focus:outline-none focus:border-purple-500 font-sans resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
            />
          </div>

          {/* Quick Questions Chips */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-white/40 mr-1 flex items-center gap-1">
              <HelpCircle className="w-3 h-3" />
              <span>Try:</span>
            </span>
            {SAMPLE_QUESTIONS.map((sq) => (
              <button
                key={sq}
                type="button"
                onClick={() => {
                  setQuestion(sq);
                  handleAsk(sq);
                }}
                disabled={isLoading}
                className="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/5 transition-colors"
              >
                {sq}
              </button>
            ))}
          </div>

          {/* Controls: Top-K Slider & Ask Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-white/5">
            <div className="flex items-center gap-3 text-xs text-white/70">
              <Sliders className="w-3.5 h-3.5 text-purple-400" />
              <span>Chunks Retrieved:</span>
              <input
                type="range"
                min={1}
                max={12}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-24 accent-purple-500"
              />
              <span className="font-mono text-purple-300 font-medium">{topK}</span>
            </div>

            <button
              onClick={() => handleAsk()}
              disabled={isLoading || !question.trim()}
              className="btn-primary px-5 py-2 rounded-xl text-xs font-medium flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Searching &amp; Reasoning...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Ask RepoMind</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* AI Answer Card */}
      {response && (
        <div className="glass-panel p-6 space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <h4 className="font-semibold text-white text-sm">RepoMind AI Explanation</h4>
            </div>
            <span className="text-xs text-purple-300 font-mono">Model: GPT-OSS 120B</span>
          </div>

          {/* Referenced files pills */}
          {response.referenced_files && response.referenced_files.length > 0 && (
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-xs text-white/50 block mb-1.5 font-medium">Referenced Files:</span>
              <div className="flex flex-wrap gap-1.5">
                {response.referenced_files.map((path) => (
                  <span
                    key={path}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-mono"
                  >
                    <FileCode className="w-3 h-3 text-purple-400" />
                    {path}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Markdown Answer */}
          <div className="bg-black/30 p-4 sm:p-5 rounded-xl border border-white/5">
            <MarkdownRenderer
              content={response.answer}
              onFileClick={onSelectFile}
            />
          </div>

          {/* Collapsible Retrieved Context */}
          <RetrievedContext hits={response.retrieval_hits} title="Retrieved Source Chunks" />
        </div>
      )}
    </div>
  );
};
