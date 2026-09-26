import type {
  CsvValidation,
  Job,
  JobDetail,
  Project,
  StartJobResponse,
  SystemInfo,
} from "./types";

export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8200"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(`Cannot reach the API at ${API_BASE}`, 0);
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* response had no JSON body */
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  system: () => request<SystemInfo>("/api/system"),

  createProject: (payload: { name: string }) =>
    request<Project>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  uploadCsv: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<CsvValidation>(`/api/projects/${projectId}/upload-csv`, {
      method: "POST",
      body: form,
    });
  },

  start: (projectId: string) =>
    request<StartJobResponse>(`/api/projects/${projectId}/start`, { method: "POST" }),

  status: (projectId: string) => request<Job | null>(`/api/projects/${projectId}/status`),

  cancel: (projectId: string) =>
    request<Job>(`/api/projects/${projectId}/cancel`, { method: "POST" }),

  job: (jobId: string) => request<JobDetail>(`/api/jobs/${jobId}`),

  jobs: () => request<Job[]>("/api/jobs"),

  retryFailed: (jobId: string) =>
    request<Job>(`/api/jobs/${jobId}/retry-failed`, { method: "POST" }),

  deleteJob: (jobId: string) => request<void>(`/api/jobs/${jobId}`, { method: "DELETE" }),

  downloadUrl: (jobId: string) => `${API_BASE}/api/jobs/${jobId}/download`,
};
