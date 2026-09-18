"use client";

import React, { useState } from "react";
import { Target, Sparkles, Loader2, FileCode, Sliders, CheckCircle2 } from "lucide-react";
import { InterviewResponse } from "@/lib/types";
import { api } from "@/lib/api";
import { RetrievedContext } from "./RetrievedContext";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";

interface InterviewTabProps {
  repoId: string;
  repoName: string;
  onSelectFile?: (filePath: string) => void;
}

const TEMPLATES: Record<string, string> = {
  "System design interview questions (repo-wide)":
    "Generate a structured interview pack for this repository: 5 system design questions, 5 code-reading questions, and 5 debugging scenarios. For each, include what a strong answer should cover. Cite file paths when relevant.",
  "Code review prompts (repo-wide)":
    "Create code review prompts for this repository: areas to scrutinize, questions to ask, risks to check (security/perf/maintainability), and suggested follow-ups. Cite file paths.",
  "Architecture deep dive questions":
    "Create an architecture interview pack for this repository: components, data flow, failure modes, trade-offs, and scaling concerns. Include 8–12 questions and a brief rubric. Cite file paths.",
};

export const InterviewTab: React.FC<InterviewTabProps> = ({ repoId, repoName, onSelectFile }) => {
  const [template, setTemplate] = useState("System design interview questions (repo-wide)");
  const [prompt, setPrompt] = useState(TEMPLATES["System design interview questions (repo-wide)"]);
  const [topK, setTopK] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<InterviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTemplateChange = (tmpl: string) => {
    setTemplate(tmpl);
    setPrompt(TEMPLATES[tmpl] || "");
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await api.generateInterview(repoId, prompt.trim(), template, topK);
      setResponse(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Interview pack generation failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Template & Prompt Configuration */}
      <div className="glass-panel p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">Interview &amp; Review Pack Generator</h3>
          </div>
          <span className="text-xs text-white/40">Evaluation Framework</span>
        </div>

        {/* Template Selector */}
        <div>
          <label className="text-xs text-white/60 block mb-1.5 font-medium">Select Evaluation Template:</label>
          <select
            value={template}
            onChange={(e) => handleTemplateChange(e.target.value)}
            className="w-full p-2.5 bg-black/40 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500 font-sans"
          >
            {Object.keys(TEMPLATES).map((key) => (
              <option key={key} value={key} className="bg-[#070a12] text-white">
                {key}
              </option>
            ))}
          </select>
        </div>

        {/* Customizable Prompt Textarea */}
        <div>
          <label className="text-xs text-white/60 block mb-1.5 font-medium">Custom Prompt &amp; Focus Area:</label>
          <textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full p-3 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-white/40 focus:outline-none focus:border-purple-500 font-sans resize-none"
          />
        </div>

        {/* Controls Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-white/5">
          <div className="flex items-center gap-3 text-xs text-white/70">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            <span>Retrieved Chunks:</span>
            <input
              type="range"
              min={3}
              max={15}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-24 accent-purple-500"
            />
            <span className="font-mono text-purple-300 font-medium">{topK}</span>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading || !prompt.trim()}
            className="btn-primary px-5 py-2 rounded-xl text-xs font-medium flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Generating Pack...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Interview Pack</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Interview Output Card */}
      {response && (
        <div className="glass-panel p-6 space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h4 className="font-semibold text-white text-sm">{response.template}</h4>
            </div>
            <span className="text-xs text-purple-300 font-mono">RepoMind Pack</span>
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

          {/* Markdown Content */}
          <div className="bg-black/30 p-4 sm:p-5 rounded-xl border border-white/5">
            <MarkdownRenderer
              content={response.answer}
              onFileClick={onSelectFile}
            />
          </div>

          {/* Retrieved context chunks */}
          <RetrievedContext hits={response.retrieval_hits} title="Supporting Retrieval Context" />
        </div>
      )}
    </div>
  );
};
