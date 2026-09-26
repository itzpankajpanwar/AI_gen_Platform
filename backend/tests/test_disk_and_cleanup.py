from datetime import timedelta

import pytest

from app.db import session_scope
from app.models import Job, JobStatus, utcnow
from app.services.disk_service import check_disk, estimate_required_bytes
from app.services.storage import JobStorage
from app.workers.cleanup_worker import run_cleanup_once
from tests.conftest import make_csv


def test_estimate_scales_with_prompt_count(settings):
    assert estimate_required_bytes(100, settings) == pytest.approx(
        10 * estimate_required_bytes(10, settings), rel=1e-6
    )


def test_disk_check_fails_when_batch_is_too_large(settings, monkeypatch):
    monkeypatch.setattr(settings, "estimated_image_mb", 10_000_000.0)
    check = check_disk(100, settings)

    assert not check.ok
    assert "Required space" in check.message
    assert "Available space" in check.message


def test_start_is_blocked_without_disk_space(client, settings, monkeypatch):
    project_id = client.post("/api/projects", json={"name": "Disk guard"}).json()["id"]
    client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("prompts.csv", make_csv(5), "text/csv")},
    )
    monkeypatch.setattr(settings, "estimated_image_mb", 10_000_000.0)

    response = client.post(f"/api/projects/{project_id}/start")

    assert response.status_code == 507
    assert "Required space" in response.json()["detail"]
    assert client.get(f"/api/projects/{project_id}/status").json() is None


def test_cleanup_removes_only_expired_jobs(client, worker, settings):
    storage = JobStorage(settings)
    job_ids = []
    for name in ("Expired batch", "Fresh batch"):
        project_id = client.post("/api/projects", json={"name": name}).json()["id"]
        client.post(
            f"/api/projects/{project_id}/upload-csv",
            files={"file": ("prompts.csv", make_csv(2), "text/csv")},
        )
        job_ids.append(client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"])
        worker.run_once()

    expired_id, fresh_id = job_ids
    with session_scope() as session:
        session.get(Job, expired_id).expires_at = utcnow() - timedelta(minutes=1)

    removed = run_cleanup_once(settings)

    assert removed == [expired_id]
    assert not storage.job_dir(expired_id).exists()
    assert storage.video_path(fresh_id).is_file()

    expired = client.get(f"/api/jobs/{expired_id}").json()
    assert expired["status"] == JobStatus.EXPIRED
    assert expired["output"] is None
    assert client.get(f"/api/jobs/{expired_id}/download").status_code == 410

    assert client.get(f"/api/jobs/{fresh_id}").json()["status"] == JobStatus.COMPLETED


def test_cleanup_is_idempotent(client, worker, settings):
    project_id = client.post("/api/projects", json={"name": "Idempotent"}).json()["id"]
    client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("prompts.csv", make_csv(1), "text/csv")},
    )
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    with session_scope() as session:
        session.get(Job, job_id).expires_at = utcnow() - timedelta(hours=1)

    assert run_cleanup_once(settings) == [job_id]
    assert run_cleanup_once(settings) == []
