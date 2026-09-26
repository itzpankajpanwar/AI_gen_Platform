"use client";

import { useRef, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import type { CsvValidation, Defaults, Job, Project } from "@/lib/types";
import { Readout } from "./ui";

interface Props {
  defaults: Defaults | null;
  onStarted: (job: Job) => void;
}

export default function SetupPanel({ defaults, onStarted }: Props) {
  const [name, setName] = useState("");
  const [project, setProject] = useState<Project | null>(null);
  const [validation, setValidation] = useState<CsvValidation | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const ready = validation?.valid === true && project !== null;

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const target = project ?? (await api.createProject({ name: name.trim() || "Untitled batch" }));
      const result = await api.uploadCsv(target.id, file);
      setProject(target);
      setValidation(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleStart() {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      const response = await api.start(project.id);
      onStarted(response.job);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start generation");
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setProject(null);
    setValidation(null);
    setError(null);
    setName("");
    if (fileInput.current) fileInput.current.value = "";
  }

  return (
    <section className="panel">
      <h2 className="panel-title">New batch</h2>
      <p className="panel-subtitle">
        One CSV in, one video out. Each prompt holds the screen for its start→end window.
      </p>

      <div className="field">
        <label htmlFor="project-name">Project name</label>
        <input
          id="project-name"
          type="text"
          placeholder="Mahindra Documentary"
          value={project ? project.name : name}
          disabled={project !== null}
          onChange={(event) => setName(event.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="csv-file">CSV file</label>
        <div
          className={`dropzone${dragging ? " is-dragging" : ""}${ready ? " is-loaded" : ""}`}
          onClick={() => fileInput.current?.click()}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            void handleFile(event.dataTransfer.files?.[0]);
          }}
        >
          {validation?.valid ? (
            <>
              <strong>
                {validation.total} scenes · {formatDuration(validation.duration_seconds)} video
              </strong>
              <span>{validation.filename}</span>
            </>
          ) : (
            <>
              <strong>{busy ? "Validating…" : "Upload CSV"}</strong>
              <span>
                Drop a file here or click to browse — columns <code>start</code>,{" "}
                <code>end</code>, <code>prompt</code>
              </span>
            </>
          )}
        </div>
        <input
          id="csv-file"
          ref={fileInput}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={(event) => void handleFile(event.target.files?.[0])}
        />
      </div>

      {validation && !validation.valid && (
        <div className="alert alert-error">
          <strong>This CSV cannot be generated</strong>
          <ul>
            {validation.errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      )}

      {validation?.warnings.map((message) => (
        <div className="alert alert-warn" key={message}>
          {message}
        </div>
      ))}

      {error && <div className="alert alert-error">{error}</div>}

      <div className="spacer" />

      <dl style={{ margin: 0 }}>
        <Readout label="Model" value={project?.model ?? defaults?.model ?? "—"} />
        <Readout
          label="Resolution"
          value={
            project
              ? `${project.width} × ${project.height}`
              : defaults
                ? `${defaults.width} × ${defaults.height}`
                : "—"
          }
        />
        <Readout label="Steps" value={String(project?.steps ?? defaults?.steps ?? "—")} />
        <Readout
          label="Format"
          value={(project?.image_format ?? defaults?.image_format ?? "png").toUpperCase()}
        />
      </dl>

      <div className="actions">
        <button className="btn-primary" onClick={handleStart} disabled={!ready || busy}>
          {busy ? "Working…" : "Start generation"}
        </button>
        {project && (
          <button className="btn-ghost" onClick={reset} disabled={busy} style={{ flex: "0 0 auto" }}>
            Start over
          </button>
        )}
      </div>
    </section>
  );
}
