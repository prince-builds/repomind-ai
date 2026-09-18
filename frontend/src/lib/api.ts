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

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface FetchOptions extends RequestInit {
  timeoutMs?: number;
}

const DEFAULT_TIMEOUT_MS = 60000;
const ANALYZE_TIMEOUT_MS = 150000;

async function fetchJson<T>(endpoint: string, options?: FetchOptions): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const { timeoutMs: _, ...fetchOptions } = options || {};
    const res = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions?.headers,
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

    if (err instanceof Error) {
      if (err.name === "AbortError") {
        throw new ApiError(
          "Request timed out while waiting for the backend response. Please try again shortly.",
          408
        );
      }
      if (err.message.includes("Failed to fetch") || err.name === "TypeError") {
        throw new ApiError(
          "The backend may be waking up or restarting due to limited resources. Please try again shortly.",
          503
        );
      }
      throw new ApiError(err.message, 500);
    }

    throw new ApiError("Failed to connect to backend server.", 500);
  } finally {
    clearTimeout(timer);
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
      timeoutMs: ANALYZE_TIMEOUT_MS,
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
