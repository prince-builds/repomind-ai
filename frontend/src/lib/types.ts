/**
 * TypeScript definitions for RepoMind AI API.
 */

export interface RetrievalHit {
  repo_name: string;
  file_path: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface AnalyzeResponse {
  repo_id: string;
  repo_name: string;
  owner: string;
  repo: string;
  clone_url: string;
  local_path: string;
  was_cloned: boolean;
  scanned_files_count: number;
  parsed_files_count: number;
  chunks_count: number;
  vectors_indexed: number;
  embedding_dim: number;
  status: string;
}

export interface OverviewMetrics {
  files_indexed: number;
  chunks_created: number;
  dependencies_found: number;
  classes_detected: number;
  functions_detected: number;
  entry_points_count: number;
  vectors_indexed: number;
  embedding_dim: number;
  skipped_unsupported: number;
  skipped_unreadable: number;
}

export interface ChunkPreview {
  file_path: string;
  chunk_index: number;
  char_count: number;
  content: string;
}

export interface OverviewResponse {
  repo_id: string;
  repo_name: string;
  owner: string;
  repo: string;
  local_path: string;
  was_cloned: boolean;
  metrics: OverviewMetrics;
  architecture_summary: string | null;
  chunk_previews: ChunkPreview[];
  supported_extensions: string[];
}

export interface FileConnection {
  file_path: string;
  inbound: number;
  outbound: number;
  total: number;
}

export interface DependencyEdge {
  source: string;
  target: string;
  is_internal: boolean;
}

export interface ArchitectureResponse {
  repo_id: string;
  repo_name: string;
  files_analyzed: number;
  internal_dependencies: number;
  external_imports: number;
  entry_points: string[];
  top_connected: FileConnection[];
  dependencies: DependencyEdge[];
  dot_graph: string;
  architecture_summary: string | null;
  raw_context_text: string;
}

export interface FileTreeNode {
  [key: string]: string | FileTreeNode;
}

export interface FileListResponse {
  repo_id: string;
  total_files: number;
  filtered_count: number;
  paths: string[];
  tree: FileTreeNode;
}

export interface AnalyzeFileResponse {
  file_path: string;
  repo_name: string;
  answer: string;
  related_files: string[];
  retrieval_hits: RetrievalHit[];
}

export interface QAResponse {
  question: string;
  repo_name: string;
  answer: string;
  referenced_files: string[];
  retrieval_hits: RetrievalHit[];
}

export interface InterviewResponse {
  template: string;
  prompt: string;
  repo_name: string;
  answer: string;
  referenced_files: string[];
  retrieval_hits: RetrievalHit[];
}
