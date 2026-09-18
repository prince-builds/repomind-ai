/**
 * API client for interacting with the RepoMind AI FastAPI backend.
 */

import {
  AnalyzeResponse,
  ArchitectureResponse,
  FileListResponse,
  AnalyzeFileResponse,
  InterviewResponse,
  OverviewResponse,
  QAResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMsg = errorData.detail;
        }
      } catch {
        // use fallback text
      }
      throw new ApiError(errorMsg, res.status);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : "Failed to connect to backend server";
    throw new ApiError(message, 500);
  }
}

export const api = {
  async checkHealth(): Promise<{ status: string; version: string }> {
    return fetchJson<{ status: string; version: string }>("/health");
  },

  async analyzeRepository(url: string): Promise<AnalyzeResponse> {
    return fetchJson<AnalyzeResponse>("/api/repositories/analyze", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  },

  async getOverview(repoId: string): Promise<OverviewResponse> {
    return fetchJson<OverviewResponse>(`/api/repositories/${encodeURIComponent(repoId)}/overview`);
  },

  async getArchitecture(repoId: string): Promise<ArchitectureResponse> {
    return fetchJson<ArchitectureResponse>(`/api/repositories/${encodeURIComponent(repoId)}/architecture`);
  },

  async getFiles(repoId: string, query: string = ""): Promise<FileListResponse> {
    const q = query ? `?query=${encodeURIComponent(query)}` : "";
    return fetchJson<FileListResponse>(`/api/repositories/${encodeURIComponent(repoId)}/files${q}`);
  },

  async analyzeFile(repoId: string, filePath: string): Promise<AnalyzeFileResponse> {
    return fetchJson<AnalyzeFileResponse>(`/api/repositories/${encodeURIComponent(repoId)}/files/analyze`, {
      method: "POST",
      body: JSON.stringify({ file_path: filePath }),
    });
  },

  async askQuestion(repoId: string, question: string, topK: number = 5): Promise<QAResponse> {
    return fetchJson<QAResponse>(`/api/repositories/${encodeURIComponent(repoId)}/qa`, {
      method: "POST",
      body: JSON.stringify({ question, top_k: topK }),
    });
  },

  async generateInterview(
    repoId: string,
    prompt: string,
    template: string,
    topK: number = 7
  ): Promise<InterviewResponse> {
    return fetchJson<InterviewResponse>(`/api/repositories/${encodeURIComponent(repoId)}/interview`, {
      method: "POST",
      body: JSON.stringify({ prompt, template, top_k: topK }),
    });
  },

  async clearSession(repoId: string, deleteDisk: boolean = false): Promise<{ repo_id: string; status: string }> {
    return fetchJson<{ repo_id: string; status: string }>(
      `/api/repositories/${encodeURIComponent(repoId)}/clear`,
      {
        method: "POST",
        body: JSON.stringify({ delete_disk_cache: deleteDisk }),
      }
    );
  },
};
