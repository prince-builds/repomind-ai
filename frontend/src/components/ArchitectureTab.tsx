"use client";

import React, { useState } from "react";
import {
  Network,
  GitBranch,
  Layers,
  ArrowRight,
  ArrowDown,
  Sparkles,
  LogIn,
  FileCode,
  Share2,
  ShieldCheck,
  Zap,
  Activity,
  Box,
  Compass,
} from "lucide-react";
import { ArchitectureResponse, FileListResponse } from "@/lib/types";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import { inferDataFlow, inferArchitectureInsights, inferRepositoryStructure } from "@/lib/analyzer";

interface ArchitectureTabProps {
  data: ArchitectureResponse;
  filesData?: FileListResponse | null;
  onSelectFile?: (filePath: string) => void;
}

export const ArchitectureTab: React.FC<ArchitectureTabProps> = ({
  data,
  filesData,
  onSelectFile,
}) => {
  const [showDot, setShowDot] = useState(false);

  // Inferred dynamic flow & insights from actual dependency relationships
  const flowSteps = React.useMemo(() => inferDataFlow(data), [data]);
  const insights = React.useMemo(() => inferArchitectureInsights(data), [data]);
  const allPaths = filesData?.paths || [];
  const layers = React.useMemo(() => inferRepositoryStructure(allPaths), [allPaths]);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* A. Architecture Overview Explanation */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Architecture Blueprint &bull; System Design Explanation
            </h3>
          </div>
          <span className="text-xs text-purple-300 font-mono">RepoMind Architecture Engine</span>
        </div>

        {data.architecture_summary ? (
          <div className="bg-black/30 p-4 sm:p-5 rounded-xl border border-white/5">
            <MarkdownRenderer
              content={data.architecture_summary}
              onFileClick={onSelectFile}
            />
          </div>
        ) : (
          <div className="bg-black/30 p-4 sm:p-5 rounded-xl border border-white/5">
            <MarkdownRenderer
              content={data.raw_context_text}
              onFileClick={onSelectFile}
            />
          </div>
        )}
      </div>

      {/* B. Application / Data Flow Diagram */}
      <div className="glass-panel p-6 border-white/10 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Application &amp; Dependency Execution Flow
            </h3>
          </div>
          <span className="text-xs text-white/40">Derived from AST Import Graph</span>
        </div>

        {flowSteps.length > 0 ? (
          <div className="space-y-3">
            {flowSteps.map((step, idx) => (
              <React.Fragment key={step.stage}>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-purple-500/15 border border-purple-500/30 text-[11px] font-mono text-purple-300 font-medium">
                        {step.badge}
                      </span>
                      <h4 className="text-xs font-semibold text-white tracking-tight">{step.stage}</h4>
                    </div>
                    <p className="text-xs text-white/60">{step.description}</p>
                  </div>

                  <div className="flex flex-wrap gap-1.5 self-stretch sm:self-auto justify-start sm:justify-end">
                    {step.files.map((fp) => (
                      <button
                        key={fp}
                        type="button"
                        onClick={() => onSelectFile?.(fp)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-black/40 hover:bg-purple-500/20 border border-white/10 hover:border-purple-500/30 text-xs font-mono text-white/80 hover:text-purple-200 transition-colors"
                        title={`Inspect ${fp} in File Intelligence`}
                      >
                        <FileCode className="w-3 h-3 text-white/40" />
                        <span>{fp}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {idx < flowSteps.length - 1 && (
                  <div className="flex justify-center py-0.5">
                    <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                      <ArrowDown className="w-3.5 h-3.5 text-purple-400" />
                    </div>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div className="text-xs text-white/40 italic p-3 text-center">
            Linear dependency flow could not be derived from this repository&apos;s import structure.
          </div>
        )}
      </div>

      {/* C. Architecture Layers */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">
              Architectural Subsystems &amp; Layers
            </h3>
          </div>
          <span className="text-xs text-white/40 font-mono">
            {layers.length} subsystem layers identified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {layers.map((layer) => (
            <div
              key={layer.name}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="px-2 py-0.5 rounded bg-white/5 text-[11px] font-mono text-emerald-300 font-medium border border-white/5">
                    {layer.badge}
                  </span>
                  <span className="text-[11px] font-mono text-white/40">{layer.totalFiles} files</span>
                </div>
                <h4 className="text-xs font-semibold text-white tracking-tight">{layer.name}</h4>
                <p className="text-[11px] text-white/60 mt-1 leading-snug">{layer.description}</p>
              </div>

              <div className="flex flex-wrap gap-1 pt-2 border-t border-white/5">
                {layer.filePaths.slice(0, 3).map((fp) => (
                  <button
                    key={fp}
                    type="button"
                    onClick={() => onSelectFile?.(fp)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-black/40 hover:bg-purple-500/20 border border-white/5 hover:border-purple-500/30 text-[10px] font-mono text-white/70 hover:text-purple-200 transition-colors"
                  >
                    <span className="truncate max-w-[130px]">{fp}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* D. RepoMind Architecture Insights */}
      <div className="glass-panel p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="font-semibold text-white text-sm tracking-tight">RepoMind Structural Insights</h3>
          </div>
          <span className="text-xs text-white/40">Graph-derived intelligence</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Primary Entry Point */}
          {insights.primaryEntryPoint && (
            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5">
              <span className="text-[11px] text-white/40 font-mono block">PRIMARY ENTRYPOINT</span>
              <button
                type="button"
                onClick={() => onSelectFile?.(insights.primaryEntryPoint!)}
                className="font-mono text-xs text-emerald-300 hover:underline font-semibold block truncate text-left w-full"
              >
                {insights.primaryEntryPoint}
              </button>
              <p className="text-[11px] text-white/60">Execution root or bootstrap runner</p>
            </div>
          )}

          {/* Primary Hub */}
          {insights.primaryHub && (
            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5">
              <span className="text-[11px] text-white/40 font-mono block">PRIMARY HUB</span>
              <button
                type="button"
                onClick={() => onSelectFile?.(insights.primaryHub!.file_path)}
                className="font-mono text-xs text-purple-300 hover:underline font-semibold block truncate text-left w-full"
              >
                {insights.primaryHub.file_path}
              </button>
              <p className="text-[11px] text-white/60">
                {insights.primaryHub.total} connections ({insights.primaryHub.inbound} inbound)
              </p>
            </div>
          )}

          {/* Potential Hotspot */}
          {insights.hotspot && (
            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5">
              <span className="text-[11px] text-white/40 font-mono block">HIGH COUPLING NODE</span>
              <button
                type="button"
                onClick={() => onSelectFile?.(insights.hotspot!.file_path)}
                className="font-mono text-xs text-rose-300 hover:underline font-semibold block truncate text-left w-full"
              >
                {insights.hotspot.file_path}
              </button>
              <p className="text-[11px] text-white/60">
                {insights.hotspot.inbound} in &bull; {insights.hotspot.outbound} out
              </p>
            </div>
          )}

          {/* External Integrations */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5">
            <span className="text-[11px] text-white/40 font-mono block">EXTERNAL BOUNDARY</span>
            <div className="font-mono text-xs text-cyan-300 font-semibold">
              {data.external_imports} external imports
            </div>
            <p className="text-[11px] text-white/60">Third-party libraries &amp; frameworks</p>
          </div>
        </div>
      </div>

      {/* E. Preserved Technical Analysis (Stats, Top Connected Table, DOT) */}
      <div className="space-y-6 pt-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white/40 pb-1 border-b border-white/5">
          <Activity className="w-3.5 h-3.5 text-purple-400" />
          <span>Technical Metrics &amp; Dependency Graph</span>
        </div>

        {/* Technical Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="glass-panel p-3.5">
            <span className="text-xs text-white/50 block font-medium">Files Analyzed</span>
            <div className="text-xl font-bold text-white tracking-tight">{data.files_analyzed}</div>
          </div>
          <div className="glass-panel p-3.5">
            <span className="text-xs text-white/50 block font-medium">Internal Dependencies</span>
            <div className="text-xl font-bold text-purple-400 tracking-tight">{data.internal_dependencies}</div>
          </div>
          <div className="glass-panel p-3.5">
            <span className="text-xs text-white/50 block font-medium">External Imports</span>
            <div className="text-xl font-bold text-cyan-400 tracking-tight">{data.external_imports}</div>
          </div>
          <div className="glass-panel p-3.5">
            <span className="text-xs text-white/50 block font-medium">Entry Candidates</span>
            <div className="text-xl font-bold text-emerald-400 tracking-tight">{data.entry_points.length}</div>
          </div>
        </div>

        {/* Top Connected Files & Graphviz DOT */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Connected Table */}
          <div className="lg:col-span-2 glass-panel p-5">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
              <h4 className="font-semibold text-white text-xs tracking-tight uppercase">Top Connected Hub Files</h4>
              <span className="text-xs text-white/40 font-mono">Ranked by Connection Volume</span>
            </div>

            {data.top_connected && data.top_connected.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-white/10 text-white/50 font-medium">
                      <th className="pb-2 font-normal">File Path</th>
                      <th className="pb-2 font-normal text-right">Inbound</th>
                      <th className="pb-2 font-normal text-right">Outbound</th>
                      <th className="pb-2 font-normal text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                    {data.top_connected.map((file, i) => (
                      <tr key={file.file_path} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-2 pr-2 text-white/90 truncate max-w-[280px]">
                          <span className="text-white/40 mr-2">#{i + 1}</span>
                          <button
                            type="button"
                            onClick={() => onSelectFile?.(file.file_path)}
                            className="text-purple-300 hover:text-purple-100 hover:underline"
                          >
                            {file.file_path}
                          </button>
                        </td>
                        <td className="py-2 px-2 text-right text-emerald-400 font-semibold">{file.inbound}</td>
                        <td className="py-2 px-2 text-right text-cyan-400">{file.outbound}</td>
                        <td className="py-2 px-2 text-right text-white font-bold">{file.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-xs text-white/40 italic p-3 text-center">
                No internal relationships detected.
              </div>
            )}
          </div>

          {/* Possible Entry Points List */}
          <div className="glass-panel p-5 flex flex-col">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
              <LogIn className="w-4 h-4 text-emerald-400" />
              <h4 className="font-semibold text-white text-xs tracking-tight uppercase">Entry Point Candidates</h4>
            </div>

            <div className="flex-1 space-y-1.5 overflow-y-auto max-h-[220px] pr-1">
              {data.entry_points && data.entry_points.length > 0 ? (
                data.entry_points.map((path) => (
                  <button
                    key={path}
                    type="button"
                    onClick={() => onSelectFile?.(path)}
                    className="w-full text-left flex items-center gap-2 p-2 rounded-lg bg-white/[0.02] hover:bg-purple-500/15 border border-white/5 hover:border-purple-500/30 text-xs font-mono text-emerald-300 hover:text-purple-200 transition-colors"
                  >
                    <FileCode className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="truncate">{path}</span>
                  </button>
                ))
              ) : (
                <div className="text-xs text-white/40 italic">No entry point candidates found.</div>
              )}
            </div>
          </div>
        </div>

        {/* Graphviz DOT / Edge exploration */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Share2 className="w-4 h-4 text-cyan-400" />
              <h4 className="font-semibold text-white text-xs tracking-tight uppercase">
                Dependency Graph ({data.dependencies.length} Edges)
              </h4>
            </div>

            <button
              onClick={() => setShowDot(!showDot)}
              className="text-xs px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 transition-colors font-mono"
            >
              {showDot ? "View Edge List" : "View Graphviz DOT"}
            </button>
          </div>

          {showDot ? (
            <pre className="p-4 rounded-xl bg-black/60 text-emerald-400 font-mono text-xs overflow-x-auto border border-white/5 max-h-[300px]">
              <code>{data.dot_graph}</code>
            </pre>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[260px] overflow-y-auto pr-1">
              {data.dependencies.slice(0, 50).map((edge, i) => (
                <div
                  key={`${edge.source}-${edge.target}-${i}`}
                  className="p-2 rounded-lg bg-black/30 border border-white/5 flex items-center justify-between gap-2 text-xs font-mono"
                >
                  <button
                    type="button"
                    onClick={() => onSelectFile?.(edge.source)}
                    className="text-white/80 hover:text-purple-300 truncate text-[11px] text-left"
                  >
                    {edge.source}
                  </button>
                  <ArrowRight className="w-3 h-3 text-purple-400 shrink-0" />
                  <button
                    type="button"
                    onClick={() => onSelectFile?.(edge.target)}
                    className="text-purple-300 hover:text-purple-100 truncate text-[11px] text-right"
                  >
                    {edge.target}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
