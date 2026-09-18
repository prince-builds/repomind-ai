"use client";

import React, { useState } from "react";
import {
  LayoutDashboard,
  Network,
  FolderTree,
  MessageSquareCode,
  Target,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { AnalyzeBar } from "@/components/AnalyzeBar";
import { OverviewTab } from "@/components/OverviewTab";
import { ArchitectureTab } from "@/components/ArchitectureTab";
import { FilesTab } from "@/components/FilesTab";
import { QATab } from "@/components/QATab";
import { InterviewTab } from "@/components/InterviewTab";
import {
  AnalyzeResponse,
  OverviewResponse,
  ArchitectureResponse,
  FileListResponse,
} from "@/lib/types";
import { api } from "@/lib/api";

type TabKey = "overview" | "architecture" | "files" | "qa" | "interview";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [currentUrl, setCurrentUrl] = useState("");
  const [activeRepoId, setActiveRepoId] = useState<string | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stored state for active analyzed repository
  const [analyzeData, setAnalyzeData] = useState<AnalyzeResponse | null>(null);
  const [overviewData, setOverviewData] = useState<OverviewResponse | null>(null);
  const [architectureData, setArchitectureData] = useState<ArchitectureResponse | null>(null);
  const [filesData, setFilesData] = useState<FileListResponse | null>(null);

  const handleSelectFile = (filePath: string) => {
    // Clean file path if it has leading/trailing characters
    const cleanPath = filePath.trim().replace(/^[`'"]+|[`'"]+$/g, "");
    setSelectedFilePath(cleanPath);
    setActiveTab("files");
  };

  const handleAnalyze = async (url: string) => {
    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setCurrentUrl(trimmed);

    try {
      // 1. Trigger analysis / index build
      const res = await api.analyzeRepository(trimmed);
      setAnalyzeData(res);
      setActiveRepoId(res.repo_id);

      // 2. Fetch overview, architecture, and files concurrently
      const [overviewRes, archRes, filesRes] = await Promise.all([
        api.getOverview(res.repo_id),
        api.getArchitecture(res.repo_id),
        api.getFiles(res.repo_id),
      ]);

      setOverviewData(overviewRes);
      setArchitectureData(archRes);
      setFilesData(filesRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyze repository.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    if (!activeRepoId) return;
    setIsClearing(true);
    try {
      await api.clearSession(activeRepoId, false);
      setActiveRepoId(null);
      setAnalyzeData(null);
      setOverviewData(null);
      setArchitectureData(null);
      setFilesData(null);
      setSelectedFilePath(null);
      setCurrentUrl("");
    } catch (err: unknown) {
      console.error("Clear failed:", err);
    } finally {
      setIsClearing(false);
    }
  };

  const tabs = [
    { key: "overview" as TabKey, label: "Overview", icon: LayoutDashboard },
    { key: "architecture" as TabKey, label: "Architecture", icon: Network },
    { key: "files" as TabKey, label: "File Intelligence", icon: FolderTree },
    { key: "qa" as TabKey, label: "Repository Q&A", icon: MessageSquareCode },
    { key: "interview" as TabKey, label: "Interview Pack", icon: Target },
  ];

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navbar */}
      <Navbar
        currentRepo={analyzeData?.repo_name || null}
        onClear={handleClear}
        isClearing={isClearing}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Hero & Ingestion Search Bar */}
        <AnalyzeBar
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          activeUrl={currentUrl}
        />

        {/* Global Error Banner */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3 max-w-3xl mx-auto">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-rose-200">Analysis Error</div>
              <div className="mt-0.5 text-xs text-rose-300/90">{error}</div>
            </div>
          </div>
        )}

        {/* Tab Navigation & Active Workspace */}
        {activeRepoId && overviewData && architectureData && filesData && !isLoading && (
          <div className="space-y-6">
            {/* Custom Tab Switcher */}
            <div className="flex items-center justify-center">
              <div className="inline-flex p-1.5 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-xl shadow-2xl">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.key;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
                        isActive
                          ? "bg-purple-600/30 text-white border border-purple-500/40 shadow-lg shadow-purple-500/20"
                          : "text-white/60 hover:text-white hover:bg-white/5"
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? "text-purple-400" : "text-white/50"}`} />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tab Panes */}
            <div className="animate-in fade-in duration-300">
              {activeTab === "overview" && (
                <OverviewTab
                  repoId={activeRepoId}
                  data={overviewData}
                  architectureData={architectureData}
                  filesData={filesData}
                  onSelectFile={handleSelectFile}
                />
              )}
              {activeTab === "architecture" && (
                <ArchitectureTab
                  data={architectureData}
                  filesData={filesData}
                  onSelectFile={handleSelectFile}
                />
              )}
              {activeTab === "files" && (
                <FilesTab
                  repoId={activeRepoId}
                  filesData={filesData}
                  selectedFilePath={selectedFilePath}
                />
              )}
              {activeTab === "qa" && (
                <QATab
                  repoId={activeRepoId}
                  repoName={overviewData.repo_name}
                  onSelectFile={handleSelectFile}
                />
              )}
              {activeTab === "interview" && (
                <InterviewTab
                  repoId={activeRepoId}
                  repoName={overviewData.repo_name}
                  onSelectFile={handleSelectFile}
                />
              )}
            </div>
          </div>
        )}

        {/* Loading Skeleton */}
        {isLoading && (
          <div className="glass-panel p-12 text-center space-y-4 max-w-lg mx-auto">
            <Loader2 className="w-10 h-10 animate-spin text-purple-400 mx-auto" />
            <div>
              <h3 className="text-base font-bold text-white">Analyzing Repository</h3>
              <p className="text-xs text-white/50 mt-1 max-w-sm mx-auto">
                Cloning git tree, parsing AST dependencies, computing FastEmbed embeddings, building FAISS search index, and generating Groq AI architecture insights...
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-white/5 text-center text-xs text-white/40">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>RepoMind AI &bull; Intelligent Codebase Exploration Engine</span>
          <span className="font-mono text-[11px] text-white/30">FastAPI Backend + Next.js UI</span>
        </div>
      </footer>
    </div>
  );
}
