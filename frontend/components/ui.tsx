import type { JobStatus } from "@/lib/types";

export function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: "success" | "danger" | "accent";
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className={`stat-value${tone ? ` ${tone}` : ""}`}>{value}</div>
    </div>
  );
}

export function Readout({ label, value }: { label: string; value: string }) {
  return (
    <div className="readout">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="progress-track">
      <div
        className="progress-fill"
        style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}

export function StatusPill({ status }: { status: JobStatus }) {
  return <span className={`status-pill ${status}`}>{status}</span>;
}

export function Chip({
  tone,
  children,
}: {
  tone?: "ok" | "bad" | "busy";
  children: React.ReactNode;
}) {
  return (
    <span className="chip">
      <span className={`dot${tone ? ` ${tone}` : ""}`} />
      {children}
    </span>
  );
}
