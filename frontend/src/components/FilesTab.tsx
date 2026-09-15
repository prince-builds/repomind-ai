"use client";

import React, { useState, useEffect } from "react";
import {
  Folder,
  FolderOpen,
  FileCode,
  Search,
  Sparkles,
  Loader2,
  FileQuestion,
  Network,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { FileListResponse, AnalyzeFileResponse, FileTreeNode } from "@/lib/types";
import { api } from "@/lib/api";
import { RetrievedContext } from "./RetrievedContext";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";

interface FilesTabProps {
  repoId: string;
  filesData: FileListResponse;
  selectedFilePath?: string | null;
}

interface TreeNodeProps {
  name: string;
  node: string | FileTreeNode;
  pathPrefix: string;
  selectedFile: string | null;
  onSelect: (path: string) => void;
}

const TreeNodeItem: React.FC<TreeNodeProps> = ({
  name,
  node,
  pathPrefix,
  selectedFile,
  onSelect,
}) => {
  const isLeaf = typeof node === "string";
  const [isOpen, setIsOpen] = useState(true);

  if (isLeaf) {
    const isSelected = selectedFile === node;
    return (
      <button
        onClick={() => onSelect(node)}
        className={`w-full text-left flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors ${
          isSelected
            ? "bg-purple-500/20 text-purple-200 border border-purple-500/30"
            : "text-white/70 hover:bg-white/5 hover:text-white"
        }`}
      >
        <FileCode className={`w-3.5 h-3.5 shrink-0 ${isSelected ? "text-purple-400" : "text-white/40"}`} />
        <span className="truncate">{name}</span>
      </button>
    );
  }

  const childKeys = Object.keys(node).sort();

  return (
    <div className="space-y-0.5">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full text-left flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium text-white/80 hover:bg-white/5 transition-colors"
      >
        {isOpen ? (
          <ChevronDown className="w-3.5 h-3.5 text-white/40" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-white/40" />
        )}
        {isOpen ? (
          <FolderOpen className="w-3.5 h-3.5 text-purple-400" />
        ) : (
          <Folder className="w-3.5 h-3.5 text-purple-400" />
        )}
        <span className="truncate">{name}</span>
        <span className="text-[10px] text-white/30 ml-auto font-mono">({childKeys.length})</span>
      </button>

      {isOpen && (
        <div className="pl-3.5 border-l border-white/5 ml-2.5 space-y-0.5">
          {childKeys.map((key) => (
            <TreeNodeItem
              key={`${pathPrefix}/${key}`}
              name={key}
              node={node[key]}
              pathPrefix={`${pathPrefix}/${key}`}
              selectedFile={selectedFile}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const FilesTab: React.FC<FilesTabProps> = ({ repoId, filesData, selectedFilePath }) => {
  const [query, setQuery] = useState("");
  const [treeData, setTreeData] = useState<FileListResponse>(filesData);
  const [selectedFile, setSelectedFile] = useState<string | null>(
    selectedFilePath || (filesData.paths.length > 0 ? filesData.paths[0] : null)
  );
  const [analysis, setAnalysis] = useState<AnalyzeFileResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cached per-file analysis map in memory
  const [cache, setCache] = useState<Record<string, AnalyzeFileResponse>>({});

  useEffect(() => {
    if (selectedFilePath && selectedFilePath !== selectedFile) {
      setSelectedFile(selectedFilePath);
      if (cache[selectedFilePath]) {
        setAnalysis(cache[selectedFilePath]);
      } else {
        setAnalysis(null);
      }
    }
  }, [selectedFilePath]);

  useEffect(() => {
    let active = true;
    const timeout = setTimeout(async () => {
      try {
        const res = await api.getFiles(repoId, query);
        if (active) {
          setTreeData(res);
        }
      } catch (err: unknown) {
        console.error("Filter files failed:", err);
      }
    }, 200);

    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [query, repoId]);

  const handleSelectFile = (path: string) => {
    setSelectedFile(path);
    setError(null);
    if (cache[path]) {
      setAnalysis(cache[path]);
    } else {
      setAnalysis(null);
    }
  };

  const handleAnalyzeFile = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const res = await api.analyzeFile(repoId, selectedFile);
      setAnalysis(res);
      setCache((prev) => ({ ...prev, [selectedFile]: res }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "File analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Sidebar: File Tree & Filter */}
      <div className="lg:col-span-4 glass-panel p-4 flex flex-col max-h-[750px]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Folder className="w-4 h-4 text-purple-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">Repository Tree</h3>
          </div>
          <span className="text-[11px] text-white/40 font-mono">
            {treeData.filtered_count} / {treeData.total_files} files
          </span>
        </div>

        {/* Filter Input */}
        <div className="relative mb-3">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/40" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter files (e.g. app.py, router)"
            className="w-full pl-8 pr-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-white placeholder-white/40 focus:outline-none focus:border-purple-500 font-mono"
          />
        </div>

        {/* Tree View */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-1">
          {Object.keys(treeData.tree).length > 0 ? (
            Object.keys(treeData.tree)
              .sort()
              .map((key) => (
                <TreeNodeItem
                  key={key}
                  name={key}
                  node={treeData.tree[key]}
                  pathPrefix={key}
                  selectedFile={selectedFile}
                  onSelect={handleSelectFile}
                />
              ))
          ) : (
            <div className="text-xs text-white/40 italic p-3 text-center">
              No files matching &quot;{query}&quot;
            </div>
          )}
        </div>
      </div>

      {/* Right Detail Pane: File Intelligence */}
      <div className="lg:col-span-8 space-y-4">
        {selectedFile ? (
          <div className="glass-panel p-5">
            {/* Header / Action Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/5 mb-5">
              <div className="flex items-center gap-2.5">
                <FileCode className="w-5 h-5 text-purple-400" />
                <div>
                  <h3 className="font-mono text-sm text-purple-200 font-semibold">{selectedFile}</h3>
                  <span className="text-xs text-white/40">File Intelligence &bull; Groq AI Deep Analysis</span>
                </div>
              </div>

              <button
                onClick={handleAnalyzeFile}
                disabled={isAnalyzing}
                className="btn-primary px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-2 justify-center"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing File...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{analysis ? "Re-Analyze File" : "Analyze File"}</span>
                  </>
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs mb-4">
                {error}
              </div>
            )}

            {/* Content Display */}
            {analysis ? (
              <div className="space-y-5">
                {/* Related files pills */}
                {analysis.related_files && analysis.related_files.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="flex items-center gap-1.5 text-xs text-white/60 mb-2 font-medium">
                      <Network className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Related Files (Dependency Expansion):</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.related_files.map((path) => (
                        <button
                          key={path}
                          onClick={() => handleSelectFile(path)}
                          className="px-2.5 py-1 rounded-md bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-[11px] font-mono border border-white/5 transition-colors"
                        >
                          {path}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Groq AI Explanation */}
                <div className="bg-black/30 p-4 sm:p-5 rounded-xl border border-white/5">
                  <MarkdownRenderer
                    content={analysis.answer}
                    onFileClick={handleSelectFile}
                  />
                </div>

                {/* Retrieved Context Chunks */}
                <RetrievedContext hits={analysis.retrieval_hits} title="File Source & Neighbor Chunks" />
              </div>
            ) : (
              <div className="p-8 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto text-purple-400">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Generate File Intelligence</h4>
                  <p className="text-xs text-white/50 max-w-md mx-auto mt-1">
                    Click &quot;Analyze File&quot; to generate an AI breakdown of purpose, structure, dependencies, data flow, interview questions, and improvement suggestions.
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="glass-panel p-10 text-center text-white/40 text-xs italic">
            Select a file from the repository tree on the left to inspect and analyze.
          </div>
        )}
      </div>
    </div>
  );
};
