"use client";

import { useState } from "react";

import { formatCountdown, formatDateTime, formatDuration, secondsUntil } from "@/lib/format";
import type { Job } from "@/lib/types";
import { StatusPill } from "./ui";

interface Props {
  jobs: Job[];
  activeJobId: string | null;
  busy: boolean;
  onSelect: (job: Job) => void;
  onDelete: (job: Job) => void;
}

export default function HistoryTable({ jobs, activeJobId, busy, onSelect, onDelete }: Props) {
  // Two-click confirm: deleting a video is not reversible.
  const [confirming, setConfirming] = useState<string | null>(null);

  return (
    <section className="panel">
      <h2 className="panel-title">Job history</h2>
      <p className="panel-subtitle">Expired jobs disappear once their files are deleted.</p>

      {jobs.length === 0 ? (
        <div className="empty">No jobs yet.</div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Job</th>
                <th>Scenes</th>
                <th>Length</th>
                <th>Success</th>
                <th>Failed</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Started</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.job_id}>
                  <td>{job.project_name}</td>
                  <td className="mono">{job.job_id}</td>
                  <td>{job.total}</td>
                  <td>{job.output ? formatDuration(job.output.duration_seconds) : "--"}</td>
                  <td>{job.successful}</td>
                  <td>{job.failed}</td>
                  <td>
                    <StatusPill status={job.status} />
                  </td>
                  <td>
                    {job.output?.expires_at ? formatCountdown(secondsUntil(job.output.expires_at)) : "--"}
                  </td>
                  <td>{formatDateTime(job.started_at)}</td>
                  <td>
                    <div className="row-actions">
                      {job.job_id !== activeJobId && (
                        <button className="link-button" onClick={() => onSelect(job)}>
                          Open
                        </button>
                      )}
                      {confirming === job.job_id ? (
                        <>
                          <button
                            className="link-button danger"
                            disabled={busy}
                            onClick={() => {
                              onDelete(job);
                              setConfirming(null);
                            }}
                          >
                            Confirm
                          </button>
                          <button className="link-button" onClick={() => setConfirming(null)}>
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          className="link-button danger"
                          disabled={busy}
                          onClick={() => setConfirming(job.job_id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
