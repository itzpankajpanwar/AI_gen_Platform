"use client";

import { api } from "@/lib/api";
import { formatCountdown, formatDuration, secondsUntil } from "@/lib/format";
import type { Job } from "@/lib/types";
import { ProgressBar, Stat, StatusPill } from "./ui";

interface Props {
  job: Job;
  busy: boolean;
  onCancel: () => void;
  onRetry: () => void;
  onNewBatch: () => void;
}

export default function JobPanel({ job, busy, onCancel, onRetry, onNewBatch }: Props) {
  const active = job.status === "running" || job.status === "queued";
  const expiresIn = job.output ? secondsUntil(job.output.expires_at) : null;
  const videoAvailable = Boolean(job.output && job.output.available && (expiresIn ?? 0) > 0);

  return (
    <section className="panel">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          gap: 16,
          marginBottom: 20,
        }}
      >
        <div>
          <h2 className="panel-title">{job.project_name}</h2>
          <p className="panel-subtitle mono" style={{ marginBottom: 0 }}>
            {job.job_id}
          </p>
        </div>
        <StatusPill status={job.status} />
      </div>

      <div className="progress-head">
        <span className="progress-percent">{job.percent.toFixed(0)}%</span>
        <span className="progress-count">
          {job.completed} / {job.total} completed
        </span>
      </div>
      <ProgressBar percent={job.percent} />

      <div className="spacer" />

      <div className="grid grid-4">
        <Stat label="Successful" value={job.successful} tone="success" />
        <Stat label="Failed" value={job.failed} tone={job.failed ? "danger" : undefined} />
        <Stat label="Remaining" value={job.remaining} />
        <Stat label="Elapsed" value={formatDuration(job.elapsed_seconds)} />
      </div>

      {active && job.current_prompt && (
        <div className="current-prompt">
          <span>Current prompt · #{job.current_index}</span>
          {job.current_prompt}
        </div>
      )}

      {active && (
        <div className="grid grid-3" style={{ marginTop: 14 }}>
          <Stat label="Estimated remaining" value={formatDuration(job.eta_seconds)} />
          <Stat label="Total prompts" value={job.total} />
          <Stat label="Backend status" value={job.cancel_requested ? "Cancelling" : "Generating"} />
        </div>
      )}

      {job.error && <div className="alert alert-error">{job.error}</div>}

      {!active && job.output && (
        <>
          <div className="alert alert-ok" style={{ marginTop: 20 }}>
            <strong>Video ready</strong> — {formatDuration(job.output.duration_seconds)} ·{" "}
            {job.output.frame_count} scenes · {job.output.size_human} · expires in{" "}
            {formatCountdown(expiresIn)}
          </div>
          {videoAvailable && (
            <video
              className="preview-video"
              src={api.downloadUrl(job.job_id)}
              controls
              preload="metadata"
            />
          )}
        </>
      )}

      {!active && !job.output && job.status !== "expired" && (
        <div className="alert alert-warn">
          No images were produced, so no video was rendered.
          {job.failed > 0 && " Retry the failed prompts to try again."}
        </div>
      )}

      {job.status === "expired" && (
        <div className="alert alert-warn">
          This job passed its retention window — the video and temporary files were deleted.
        </div>
      )}

      <div className="actions">
        {active ? (
          <button className="btn-ghost" onClick={onCancel} disabled={busy || job.cancel_requested}>
            {job.cancel_requested ? "Cancelling…" : "Cancel generation"}
          </button>
        ) : (
          <>
            {videoAvailable && (
              <a className="btn-download" href={api.downloadUrl(job.job_id)} download>
                Download video · {job.output?.size_human}
              </a>
            )}
            {job.failed > 0 && job.status !== "expired" && (
              <button className="btn-ghost" onClick={onRetry} disabled={busy}>
                Retry {job.failed} failed
              </button>
            )}
            <button className="btn-ghost" onClick={onNewBatch} disabled={busy}>
              New batch
            </button>
          </>
        )}
      </div>
    </section>
  );
}
