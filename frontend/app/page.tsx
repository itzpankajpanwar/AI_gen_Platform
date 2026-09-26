"use client";

import { useCallback, useEffect, useState } from "react";

import HistoryTable from "@/components/HistoryTable";
import JobPanel from "@/components/JobPanel";
import SetupPanel from "@/components/SetupPanel";
import { Chip } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import type { Job, SystemInfo } from "@/lib/types";

const POLL_MS = 1500;
const HISTORY_MS = 20000;

function isActive(job: Job | null): boolean {
  return job?.status === "running" || job?.status === "queued";
}

export default function Home() {
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshHistory = useCallback(async () => {
    try {
      const [history, info] = await Promise.all([api.jobs(), api.system()]);
      setJobs(history);
      setSystem(info);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The API is unreachable");
    }
  }, []);

  useEffect(() => {
    void refreshHistory();
    const timer = setInterval(() => void refreshHistory(), HISTORY_MS);
    return () => clearInterval(timer);
  }, [refreshHistory]);

  useEffect(() => {
    if (!isActive(job) || !job) return;
    let cancelled = false;

    const timer = setInterval(async () => {
      try {
        const fresh = await api.job(job.job_id);
        if (cancelled) return;
        setJob(fresh);
        if (!isActive(fresh)) void refreshHistory();
      } catch {
        /* keep the last known state and retry on the next tick */
      }
    }, POLL_MS);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [job, refreshHistory]);

  async function handleDelete(target: Job) {
    setBusy(true);
    setError(null);
    try {
      await api.deleteJob(target.job_id);
      if (job?.job_id === target.job_id) setJob(null);
      await refreshHistory();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the job");
    } finally {
      setBusy(false);
    }
  }

  async function guard(action: () => Promise<Job>) {
    setBusy(true);
    setError(null);
    try {
      setJob(await action());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  const generatorHealthy = system?.generator.healthy ?? false;

  return (
    <main className="shell">
      <header className="masthead">
        <div>
          <h1>AI Image Generator</h1>
          <p>CSV timeline → generated images → one video, kept for 10 hours.</p>
        </div>
        <div className="masthead-meta">
          <Chip tone={generatorHealthy ? "ok" : "bad"}>
            {system ? `${system.generator_backend} backend` : "connecting…"}
          </Chip>
          {system && <Chip>{system.disk_free_human} free</Chip>}
          {system && system.active_jobs > 0 && <Chip tone="busy">{system.active_jobs} active</Chip>}
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {!generatorHealthy && system && (
        <div className="alert alert-warn">
          The <strong>{system.generator_backend}</strong> backend is not responding —{" "}
          {system.generator.detail}
        </div>
      )}

      {job ? (
        <JobPanel
          job={job}
          busy={busy}
          onCancel={() => void guard(() => api.cancel(job.project_id))}
          onRetry={() => void guard(() => api.retryFailed(job.job_id))}
          onNewBatch={() => setJob(null)}
        />
      ) : (
        <SetupPanel
          defaults={system?.defaults ?? null}
          onStarted={(started) => {
            setJob(started);
            void refreshHistory();
          }}
        />
      )}

      <HistoryTable
        jobs={jobs}
        activeJobId={job?.job_id ?? null}
        busy={busy}
        onSelect={(selected) => setJob(selected)}
        onDelete={(target) => void handleDelete(target)}
      />
    </main>
  );
}
