/**
 * Dynamic analysis helpers to infer repository structure, layered data flows,
 * and architectural insights from raw analysis data without hardcoding.
 */

import { ArchitectureResponse, DependencyEdge, FileConnection } from "./types";

export interface RepoModuleCategory {
  name: string;
  badge: string;
  description: string;
  filePaths: string[];
  totalFiles: number;
}

export interface ArchitectureLayer {
  name: string;
  badge: string;
  role: string;
  files: string[];
}

export interface FlowStep {
  stage: string;
  badge: string;
  description: string;
  files: string[];
}

export interface ArchitectureInsights {
  primaryEntryPoint: string | null;
  primaryHub: FileConnection | null;
  hotspot: FileConnection | null;
  topDependencyPath: DependencyEdge | null;
  externalImportsCount: number;
}

/**
 * Infer high-level repository structure categories from actual file paths.
 * Only returns categories that actually contain files in this repository.
 */
export function inferRepositoryStructure(paths: string[]): RepoModuleCategory[] {
  const categories: Record<string, { name: string; badge: string; description: string; paths: string[] }> = {};

  for (const path of paths) {
    const lower = path.toLowerCase();
    const parts = path.split("/");

    let catKey = "misc";
    let catName = "Other Modules";
    let catBadge = "Module";
    let catDesc = "Supporting project files and scripts";

    if (parts.length === 1) {
      if (lower.includes("app") || lower.includes("main") || lower.includes("index") || lower.includes("server")) {
        catKey = "entry";
        catName = "Application Entrypoints";
        catBadge = "Entry";
        catDesc = "Root boot scripts, runners, and entry files";
      } else if (lower.includes("readme") || lower.includes("doc") || lower.endsWith(".md")) {
        catKey = "docs";
        catName = "Documentation";
        catBadge = "Docs";
        catDesc = "Project specifications and guides";
      } else if (lower.includes("config") || lower.includes(".env") || lower.includes("docker") || lower.includes("requirements") || lower.includes("package.json")) {
        catKey = "config";
        catName = "Configuration & Build";
        catBadge = "Config";
        catDesc = "Environment and package settings";
      } else {
        catKey = "root";
        catName = "Root Files";
        catBadge = "Root";
        catDesc = "Top-level application files";
      }
    } else {
      const topDir = parts[0].toLowerCase();

      if (topDir.includes("core") || topDir.includes("service") || topDir.includes("domain") || topDir.includes("logic")) {
        catKey = "core";
        catName = `Core Business Logic (${parts[0]})`;
        catBadge = "Core";
        catDesc = "Domain services, business logic, and processing pipelines";
      } else if (topDir.includes("api") || topDir.includes("router") || topDir.includes("endpoint") || topDir.includes("controller") || topDir.includes("server")) {
        catKey = "api";
        catName = `API & Routing (${parts[0]})`;
        catBadge = "API";
        catDesc = "HTTP route handlers, endpoints, and request controllers";
      } else if (topDir.includes("retrieval") || topDir.includes("rag") || topDir.includes("embedding") || topDir.includes("vector") || topDir.includes("chunk")) {
        catKey = "rag";
        catName = `Retrieval & Intelligence (${parts[0]})`;
        catBadge = "RAG";
        catDesc = "Vector stores, semantic chunking, embeddings, and retrieval";
      } else if (topDir.includes("ui") || topDir.includes("template") || topDir.includes("component") || topDir.includes("view") || topDir.includes("frontend") || topDir.includes("src/app")) {
        catKey = "ui";
        catName = `User Interface (${parts[0]})`;
        catBadge = "UI";
        catDesc = "UI components, templates, and view layers";
      } else if (topDir.includes("util") || topDir.includes("helper") || topDir.includes("lib") || topDir.includes("common") || topDir.includes("shared")) {
        catKey = "utils";
        catName = `Utilities & Helpers (${parts[0]})`;
        catBadge = "Utils";
        catDesc = "Shared utility functions, helpers, and common libraries";
      } else if (topDir.includes("config") || topDir.includes("setting") || topDir.includes("env")) {
        catKey = "config";
        catName = `Configuration (${parts[0]})`;
        catBadge = "Config";
        catDesc = "Application settings and environment definitions";
      } else if (topDir.includes("test") || topDir.includes("spec")) {
        catKey = "tests";
        catName = `Tests & Fixtures (${parts[0]})`;
        catBadge = "Tests";
        catDesc = "Automated test suites and verification cases";
      } else if (topDir.includes("data") || topDir.includes("model") || topDir.includes("schema") || topDir.includes("db") || topDir.includes("store")) {
        catKey = "data";
        catName = `Data & Schemas (${parts[0]})`;
        catBadge = "Data";
        catDesc = "Data models, schemas, and persistence interfaces";
      } else {
        catKey = topDir;
        catName = `Package: ${parts[0]}`;
        catBadge = "Package";
        catDesc = `Internal module package under /${parts[0]}`;
      }
    }

    if (!categories[catKey]) {
      categories[catKey] = {
        name: catName,
        badge: catBadge,
        description: catDesc,
        paths: [],
      };
    }
    categories[catKey].paths.push(path);
  }

  return Object.values(categories)
    .map((c) => ({
      name: c.name,
      badge: c.badge,
      description: c.description,
      filePaths: c.paths,
      totalFiles: c.paths.length,
    }))
    .sort((a, b) => b.totalFiles - a.totalFiles);
}

/**
 * Infer layered application flow from actual dependency relationships.
 */
export function inferDataFlow(arch: ArchitectureResponse): FlowStep[] {
  const steps: FlowStep[] = [];
  const entrySet = new Set(arch.entry_points);
  const internalEdges = arch.dependencies.filter((e) => e.is_internal);

  // 1. Entrypoints Stage
  if (arch.entry_points.length > 0) {
    steps.push({
      stage: "1. Entry & Interface",
      badge: "Inbound Interface",
      description: "Initial request handling, CLI invocation, or application entry point",
      files: arch.entry_points.slice(0, 4),
    });
  }

  // 2. Direct Core Dependencies of entrypoints
  const coreTargets = new Set<string>();
  for (const edge of internalEdges) {
    if (entrySet.has(edge.source) && !entrySet.has(edge.target)) {
      coreTargets.add(edge.target);
    }
  }

  if (coreTargets.size > 0) {
    steps.push({
      stage: "2. Core Logic & Orchestration",
      badge: "Business Logic",
      description: "Intermediate coordinators, domain services, and processing modules",
      files: Array.from(coreTargets).slice(0, 5),
    });
  }

  // 3. Storage, Utils & Leaf Dependencies
  const leafTargets = new Set<string>();
  for (const edge of internalEdges) {
    if (coreTargets.has(edge.source) && !entrySet.has(edge.target) && !coreTargets.has(edge.target)) {
      leafTargets.add(edge.target);
    }
  }

  // If no second-hop leaves found, pick remaining most-connected inbound targets
  if (leafTargets.size === 0) {
    for (const conn of arch.top_connected) {
      if (!entrySet.has(conn.file_path) && !coreTargets.has(conn.file_path)) {
        leafTargets.add(conn.file_path);
      }
    }
  }

  if (leafTargets.size > 0) {
    steps.push({
      stage: "3. Persistence & Shared Infrastructure",
      badge: "Storage & Utilities",
      description: "Data stores, configurations, logging, and shared utility modules",
      files: Array.from(leafTargets).slice(0, 5),
    });
  }

  return steps;
}

/**
 * Infer architecture insights from analyzed metrics and graph.
 */
export function inferArchitectureInsights(arch: ArchitectureResponse): ArchitectureInsights {
  const primaryEntryPoint = arch.entry_points.length > 0 ? arch.entry_points[0] : null;
  const primaryHub = arch.top_connected.length > 0 ? arch.top_connected[0] : null;

  // Potential hotspot: file with high inbound + outbound that might be a monolith/chokepoint
  let hotspot: FileConnection | null = null;
  for (const conn of arch.top_connected) {
    if (conn.inbound >= 2 && conn.outbound >= 2) {
      hotspot = conn;
      break;
    }
  }
  if (!hotspot && arch.top_connected.length > 1) {
    hotspot = arch.top_connected[1];
  }

  // Top dependency path: highest-ranked edge between connected files
  let topDependencyPath: DependencyEdge | null = null;
  const internalEdges = arch.dependencies.filter((e) => e.is_internal);
  if (internalEdges.length > 0) {
    topDependencyPath = internalEdges[0];
  }

  return {
    primaryEntryPoint,
    primaryHub,
    hotspot,
    topDependencyPath,
    externalImportsCount: arch.external_imports,
  };
}
