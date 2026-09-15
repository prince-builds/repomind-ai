"use client";

import React, { useState, useMemo } from "react";
import {
  FolderGit2,
  ExternalLink,
  CheckCircle2,
  Cpu,
  Layers,
  FileText,
  Network,
  Code2,
  LogIn,
  Sparkles,
  FolderTree,
  FileCode,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Box,
  Terminal,
  Cloud,
  Server,
  Database,
  BrainCircuit,
  Zap,
  RefreshCw,
  ShieldCheck,
  Target,
  Users,
  Compass,
  CheckCircle,
} from "lucide-react";
import {
  OverviewResponse,
  ArchitectureResponse,
  FileListResponse,
} from "@/lib/types";
import { api } from "@/lib/api";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import {
  buildProductProfile,
  ProductProfile,
} from "@/lib/productProfile";

interface OverviewTabProps {
  repoId?: string | null;
  data: OverviewResponse;
  architectureData?: ArchitectureResponse | null;
  filesData?: FileListResponse | null;
  onSelectFile?: (filePath: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  repoId,
  data,
  architectureData,
  filesData,
  onSelectFile,
}) => {
  const { metrics } = data;
  const [showAllChunks, setShowAllChunks] = useState(false);
  const [isSynthesizingAI, setIsSynthesizingAI] = useState(false);
  const [aiProfileResult, setAiProfileResult] = useState<string | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  // 1. Build grounded product profile from repository evidence
  const profile: ProductProfile = useMemo(() => {
    return buildProductProfile(data, architectureData, filesData);
  }, [data, architectureData, filesData]);

  // Handle Groq AI Product Profile Synthesis
  const handleSynthesizeAI = async () => {
    if (!repoId) return;
    setIsSynthesizingAI(true);
    setAiError(null);

    const profilePrompt = `Answer the following strictly as a REPOSITORY & PRODUCT PROFILE (NOT a technical architecture explanation):

"What is this repository and what kind of product/project is it?"

Provide a structured, developer-focused profile with:
1. **Product / Project Type**: Inferred category and classification.
2. **Product Summary**: One concise paragraph explaining what the product is and its main purpose.
3. **Problem Solved**: What user/developer pain point it addresses.
4. **Intended Users & Audience**: Who this tool or application is for.
5. **Main Capabilities**: 4-6 user-facing or developer-facing core features.
6. **Technology Stack**: Technologies directly evidenced by code and configuration.
7. **Deployment & Infrastructure**: Cloud/container platforms if evidenced, or state "Deployment platform not detected from repository".

CRITICAL GROUNDING RULE:
- Distinguish between facts directly evidenced in source code/configs and claims from README.
- Never invent technologies, databases, or cloud providers without evidence.
- Do NOT turn this into an architecture call-graph explanation (architecture belongs in the Architecture tab).`;

    try {
      const res = await api.askQuestion(repoId, profilePrompt, 6);
      setAiProfileResult(res.answer);
    } catch (err: unknown) {
      setAiError(
        err instanceof Error
          ? err.message
          : "Failed to generate AI product profile. Verify GROQ_API_KEY in .env."
      );
    } finally {
      setIsSynthesizingAI(false);
    }
  };

  // Metric tiles for repository stats
  const metricTiles = [
    {
      label: "Files Indexed",
      value: metrics.files_indexed,
      icon: FileText,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
    },
    {
      label: "Chunks Created",
      value: metrics.chunks_created,
      icon: Layers,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/20",
    },
    {
      label: "Dependencies",
      value: metrics.dependencies_found,
      icon: Network,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/20",
    },
    {
      label: "Classes",
      value: metrics.classes_detected,
      icon: Code2,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
    },
    {
      label: "Functions",
      value: metrics.functions_detected,
      icon: Cpu,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
    },
    {
      label: "Entry Points",
      value: metrics.entry_points_count,
      icon: LogIn,
      color: "text-rose-400",
      bg: "bg-rose-500/10",
      border: "border-rose-500/20",
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 1. REPOSITORY IDENTITY BANNER */}
      <div className="glass-panel p-5 sm:p-6 border-white/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center justify-center shrink-0 mt-0.5 shadow-lg shadow-purple-500/10">
              <FolderGit2 className="w-6 h-6 text-purple-300" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight font-mono">
                  {data.repo_name}
                </h2>
                <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {data.was_cloned ? "Freshly Cloned" : "Loaded from Cache"}
                </span>
                <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono">
                  FAISS {metrics.vectors_indexed} Vectors ({metrics.embedding_dim}d)
                </span>
              </div>
              <p className="text-xs text-white/50 font-mono mt-1.5 break-all flex items-center gap-1.5">
                <Terminal className="w-3 h-3 text-white/40 shrink-0" />
                <span>Local path: {data.local_path}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 self-stretch sm:self-auto justify-end">
            <a
              href={`https://github.com/${data.repo_name}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/80 hover:text-white border border-white/10 text-xs font-medium transition-all hover:scale-[1.02] shadow-sm"
            >
              <span>View GitHub</span>
              <ExternalLink className="w-3.5 h-3.5 text-white/50" />
            </a>
          </div>
        </div>
      </div>

      {/* 2. REPOSITORY & PRODUCT PROFILE HERO CARD */}
      <div className="glass-panel p-6 sm:p-7 border-purple-500/20 relative overflow-hidden space-y-5 bg-gradient-to-b from-purple-950/20 to-transparent">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/10">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider font-mono">
                Product &amp; Repository Profile
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 pt-0.5">
              <span className="text-lg sm:text-xl font-bold text-white">
                {profile.projectType}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 text-[11px] font-mono border border-purple-500/30">
                {profile.projectTypeConfidence} Confidence
              </span>
            </div>
          </div>

          {/* Secondary Badges */}
          <div className="flex flex-wrap gap-1.5">
            {profile.secondaryBadges.map((badge) => (
              <span
                key={badge}
                className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-medium text-white/70"
              >
                {badge}
              </span>
            ))}
          </div>
        </div>

        {/* Product Rationale */}
        <p className="text-xs text-purple-200/70 italic">
          {profile.projectTypeRationale}
        </p>

        {/* What This Repository Does — Three Core Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-1">
          {/* Main Description */}
          <div className="lg:col-span-2 p-4 sm:p-5 rounded-xl bg-black/40 border border-white/5 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-white/90">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              <span>What This Repository Does</span>
            </div>
            <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-sans">
              {profile.productSummary}
            </p>
          </div>

          {/* Problem Solved & Target Audience */}
          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                <Target className="w-3.5 h-3.5" />
                <span>Problem Solved</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed">
                {profile.problemSolved}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400">
                <Users className="w-3.5 h-3.5" />
                <span>Intended Audience</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed">
                {profile.targetAudience}
              </p>
            </div>
          </div>
        </div>

        {/* Optional AI Profile Synthesis Section */}
        <div className="pt-2 border-t border-white/5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-white/50">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{profile.evidenceSource}</span>
            </div>

            {repoId && (
              <button
                type="button"
                onClick={handleSynthesizeAI}
                disabled={isSynthesizingAI}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-medium transition-all disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${
                    isSynthesizingAI ? "animate-spin" : ""
                  }`}
                />
                <span>
                  {isSynthesizingAI
                    ? "Synthesizing AI Profile..."
                    : aiProfileResult
                    ? "Re-synthesize AI Profile"
                    : "Ask AI for In-Depth Profile"}
                </span>
              </button>
            )}
          </div>

          {/* Render AI Result if triggered */}
          {aiProfileResult && (
            <div className="mt-4 p-4 sm:p-5 rounded-xl bg-purple-950/20 border border-purple-500/20 space-y-2">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5 text-xs font-semibold text-purple-300">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>AI-Generated Product &amp; Repository Profile (Groq Llama-3)</span>
              </div>
              <MarkdownRenderer
                content={aiProfileResult}
                onFileClick={onSelectFile}
              />
            </div>
          )}

          {aiError && (
            <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{aiError}</span>
            </div>
          )}
        </div>
      </div>

      {/* 3. KEY METRICS BAR (PRESERVED) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {metricTiles.map((tile) => {
          const Icon = tile.icon;
          return (
            <div
              key={tile.label}
              className="glass-panel p-3.5 flex flex-col justify-between hover:border-white/20 transition-colors"
            >
              <div className="flex items-center justify-between text-white/50 text-xs mb-1">
                <span>{tile.label}</span>
                <div
                  className={`w-6 h-6 rounded-md ${tile.bg} ${tile.border} border flex items-center justify-center`}
                >
                  <Icon className={`w-3.5 h-3.5 ${tile.color}`} />
                </div>
              </div>
              <div className="text-xl font-bold text-white tracking-tight font-mono">
                {tile.value.toLocaleString()}
              </div>
            </div>
          );
        })}
      </div>

      {/* 4. CORE CAPABILITIES (FEATURE CARDS) */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Core Capabilities &amp; Key Features
            </h3>
          </div>
          <span className="text-xs text-white/40 font-mono">
            {profile.capabilities.length} features evidenced
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {profile.capabilities.map((cap) => (
            <div
              key={cap.id}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-purple-500/30 transition-all space-y-2 flex flex-col justify-between group"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors">
                    {cap.title}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 text-[10px] font-mono shrink-0">
                    {cap.badge}
                  </span>
                </div>
                <p className="text-xs text-white/60 leading-relaxed">
                  {cap.description}
                </p>
              </div>

              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-white/40 font-mono">
                <span className="truncate">Source: {cap.source}</span>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400/70 shrink-0" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. TECHNOLOGY STACK (EVIDENCED ONLY) */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-cyan-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Evidenced Technology Stack
            </h3>
          </div>
          <span className="text-xs text-emerald-400/80 font-mono flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Verified from files &amp; manifests
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profile.techStackCategories.map((cat) => (
            <div
              key={cat.category}
              className="p-4 rounded-xl bg-black/30 border border-white/5 space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white/90">
                  {cat.category}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-white/5 ${cat.color}`}
                >
                  {cat.badge}
                </span>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {cat.items.map((item) => (
                  <div
                    key={item.name}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/10 hover:border-purple-500/30 text-xs font-mono text-white/80 transition-colors"
                    title={item.evidence}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                    <span>{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. DEPLOYMENT & INFRASTRUCTURE */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Cloud className="w-4 h-4 text-blue-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Deployment &amp; Infrastructure
            </h3>
          </div>
          <span className="text-xs text-white/40 font-mono">
            {profile.deployment.isDetected
              ? `${profile.deployment.platforms.length} platform(s) detected`
              : "Strict Grounding"}
          </span>
        </div>

        {profile.deployment.isDetected ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {profile.deployment.platforms.map((dep) => (
              <div
                key={dep.platform}
                className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-blue-500/30 transition-colors space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">
                    {dep.platform}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 text-[10px] font-mono">
                    {dep.badge}
                  </span>
                </div>
                <p className="text-xs text-white/60">{dep.description}</p>
                <div className="pt-2 border-t border-white/5 flex items-center gap-1.5 text-[11px] font-mono text-white/40">
                  <FileCode className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span className="truncate">{dep.configFile}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-white/[0.02] border border-dashed border-white/10 text-center space-y-1">
            <p className="text-xs font-semibold text-white/70">
              {profile.deployment.fallbackMessage}
            </p>
            <p className="text-[11px] text-white/40 max-w-lg mx-auto">
              {profile.deployment.fallbackDetail}
            </p>
          </div>
        )}
      </div>

      {/* 7. REPOSITORY STRUCTURE / MAJOR PARTS */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <FolderTree className="w-4 h-4 text-cyan-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Major Project Subsystems &amp; Functional Areas
            </h3>
          </div>
          <span className="text-xs text-white/40 font-mono">
            {profile.majorParts.length} functional areas identified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {profile.majorParts.map((part) => (
            <div
              key={part.name}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors space-y-2.5"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[11px] font-mono text-purple-300 font-medium">
                    {part.badge}
                  </span>
                  <span className="text-xs font-semibold text-white/90">
                    {part.name}
                  </span>
                </div>
                <span className="text-xs font-mono text-white/40">
                  {part.fileCount} files
                </span>
              </div>

              <p className="text-xs text-white/60 leading-relaxed">
                {part.responsibility}
              </p>

              {/* Sample file chips clickable to File Intelligence */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {part.sampleFiles.map((fp) => (
                  <button
                    key={fp}
                    type="button"
                    onClick={() => onSelectFile?.(fp)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-black/40 hover:bg-purple-500/20 border border-white/5 hover:border-purple-500/30 text-[11px] font-mono text-white/70 hover:text-purple-200 transition-colors"
                    title={`Inspect ${fp} in File Intelligence`}
                  >
                    <FileCode className="w-3 h-3 text-white/40" />
                    <span className="truncate max-w-[180px]">{fp}</span>
                  </button>
                ))}
                {part.fileCount > 4 && (
                  <span className="text-[10px] text-white/40 self-center px-1 font-mono">
                    +{part.fileCount - 4} more
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 8. KEY CENTRAL FILES */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-emerald-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Key Central Files &amp; Responsibilities
            </h3>
          </div>
          <span className="text-xs text-white/40">
            Click any file to inspect in File Intelligence
          </span>
        </div>

        {profile.keyFiles.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {profile.keyFiles.map((item) => (
              <button
                key={item.path}
                type="button"
                onClick={() => onSelectFile?.(item.path)}
                className="p-3.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-purple-500/30 text-left transition-all group flex flex-col justify-between space-y-2.5"
              >
                <div>
                  <div className="flex items-center justify-between gap-1 text-[10px] font-mono text-white/40 mb-1">
                    <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 font-medium">
                      {item.role}
                    </span>
                    {item.connections > 0 && (
                      <span>{item.connections} connections</span>
                    )}
                  </div>
                  <div className="font-mono text-xs text-white/90 group-hover:text-purple-200 font-semibold truncate">
                    {item.path}
                  </div>
                  <p className="text-[11px] text-white/50 mt-1 line-clamp-2">
                    {item.reason}
                  </p>
                </div>

                <div className="flex items-center justify-between text-[11px] text-white/50 pt-1.5 border-t border-white/5">
                  {item.connections > 0 ? (
                    <>
                      <span className="text-emerald-400">
                        {item.inbound} inbound
                      </span>
                      <span className="text-cyan-400">
                        {item.outbound} outbound
                      </span>
                    </>
                  ) : (
                    <span className="text-white/40">Primary File</span>
                  )}
                  <ArrowRight className="w-3.5 h-3.5 text-white/30 group-hover:text-purple-400 group-hover:translate-x-0.5 transition-all" />
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-xs text-white/40 italic p-3 text-center">
            No central dependency hubs identified.
          </div>
        )}
      </div>

      {/* 9 & 10. INDEXING SNAPSHOT (PLACED LOWER ON PAGE) */}
      <div className="glass-panel p-5 border-white/10 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <h4 className="font-semibold text-white text-xs tracking-tight uppercase">
              Indexing Snapshot &amp; Supported File Formats
            </h4>
          </div>

          <button
            type="button"
            onClick={() => setShowAllChunks(!showAllChunks)}
            className="text-xs text-white/60 hover:text-white flex items-center gap-1 font-mono transition-colors"
          >
            <span>{showAllChunks ? "Hide Chunks" : "Preview Index Chunks"}</span>
            {showAllChunks ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        {/* Supported Extensions Pills */}
        <div className="flex flex-wrap gap-1.5">
          {data.supported_extensions.map((ext) => (
            <span
              key={ext}
              className="px-2 py-0.5 rounded bg-white/5 border border-white/5 text-[11px] font-mono text-white/60"
            >
              {ext}
            </span>
          ))}
        </div>

        {/* Expandable Chunk Previews */}
        {showAllChunks && (
          <div className="pt-3 border-t border-white/5 space-y-2 max-h-[300px] overflow-y-auto pr-1">
            {data.chunk_previews.map((chunk) => (
              <div
                key={`${chunk.file_path}-${chunk.chunk_index}`}
                className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs space-y-1"
              >
                <div className="flex items-center justify-between text-white/70 font-mono text-[11px]">
                  <span className="text-purple-300 font-medium truncate max-w-[300px]">
                    {chunk.file_path}
                  </span>
                  <span>
                    chunk #{chunk.chunk_index} ({chunk.char_count} chars)
                  </span>
                </div>
                <pre className="p-2 rounded bg-black/60 text-white/70 font-mono text-[11px] overflow-x-auto">
                  <code>{chunk.content}</code>
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
