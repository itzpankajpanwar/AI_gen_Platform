export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "cancelled"
  | "failed"
  | "expired";

export interface Project {
  id: string;
  name: string;
  model: string;
  width: number;
  height: number;
  steps: number;
  batch_size: number;
  image_format: string;
  seed: number | null;
  csv_filename: string | null;
  prompt_count: number;
  created_at: string;
}

export interface PromptPreview {
  id: string;
  text: string;
  start_seconds: number;
  end_seconds: number;
}

export interface CsvValidation {
  valid: boolean;
  total: number;
  duration_seconds: number;
  filename: string | null;
  errors: string[];
  warnings: string[];
  preview: PromptPreview[];
}

export interface OutputInfo {
  filename: string;
  size_bytes: number;
  size_human: string;
  frame_count: number;
  duration_seconds: number;
  created_at: string | null;
  expires_at: string | null;
  expires_in_seconds: number | null;
  available: boolean;
}

export interface Job {
  job_id: string;
  project_id: string;
  project_name: string;
  status: JobStatus;
  total: number;
  successful: number;
  failed: number;
  completed: number;
  remaining: number;
  percent: number;
  current_index: number;
  current_prompt: string | null;
  cancel_requested: boolean;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  elapsed_seconds: number | null;
  eta_seconds: number | null;
  output: OutputInfo | null;
}

export interface JobItem {
  order_index: number;
  external_id: string;
  prompt_text: string;
  start_seconds: number;
  end_seconds: number;
  status: "pending" | "running" | "success" | "failed";
  filename: string | null;
  seed: number | null;
  duration_ms: number | null;
  attempts: number;
  error: string | null;
}

export interface JobDetail extends Job {
  items: JobItem[];
}

export interface Defaults {
  model: string;
  width: number;
  height: number;
  steps: number;
  batch_size: number;
  image_format: string;
  min_prompts: number;
  max_prompts: number;
  recommended_min_prompts: number;
  zip_retention_hours: number;
}

export interface SystemInfo {
  app: string;
  generator_backend: string;
  available_backends: string[];
  generator: { backend: string; healthy: boolean; detail: string };
  defaults: Defaults;
  data_dir: string;
  disk_total_bytes: number;
  disk_free_bytes: number;
  disk_free_human: string;
  worker_in_api: boolean;
  active_jobs: number;
}

export interface DiskInfo {
  ok: boolean;
  prompt_count: number;
  required_gb: number;
  available_gb: number;
  message: string;
}

export interface StartJobResponse {
  job: Job;
  disk: DiskInfo;
}
