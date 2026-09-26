from app.db import session_scope
from app.models import Job, JobStatus
from app.services.storage import JobStorage
from tests.conftest import make_csv, probe_video


def create_project_with_csv(client, name: str, count: int, seconds_each: float = 2.0) -> str:
    project_id = client.post("/api/projects", json={"name": name}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("timeline.csv", make_csv(count, seconds_each), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["total"] == count
    assert body["duration_seconds"] == count * seconds_each
    return project_id


def test_spec_example_renders_a_seven_second_video(client, worker, settings):
    """0-5s of prompt one, 5-7s of prompt two, one 7 second file."""
    project_id = client.post("/api/projects", json={"name": "Spec example"}).json()["id"]
    csv = b'start,end,prompt\n0,5,"1940s railway station at dawn"\n5,7,"steel foundry, sparks"\n'
    client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("timeline.csv", csv, "text/csv")},
    )

    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/projects/{project_id}/status").json()
    assert status["status"] == JobStatus.COMPLETED
    assert status["successful"] == 2
    assert status["output"]["duration_seconds"] == 7
    assert status["output"]["filename"] == f"{job_id}.mp4"
    assert status["output"]["frame_count"] == 2

    probed = probe_video(JobStorage(settings).video_path(job_id))
    assert probed["duration"] == __import__("pytest").approx(7, abs=0.3)
    assert (probed["width"], probed["height"]) == (192, 108)
    assert probed["codec"] == "h264"


def test_download_serves_an_mp4(client, worker):
    project_id = create_project_with_csv(client, "Download test", 3)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    response = client.get(f"/api/jobs/{job_id}/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.content[4:12] == b"ftypisom" or b"ftyp" in response.content[:32]
    assert len(response.content) > 1000


def test_longer_batch_matches_total_timeline(client, worker, settings):
    import pytest

    project_id = create_project_with_csv(client, "Mahindra Documentary", 30, seconds_each=1.5)

    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/projects/{project_id}/status").json()
    assert (status["total"], status["successful"], status["failed"]) == (30, 30, 0)
    assert status["output"]["duration_seconds"] == 45

    probed = probe_video(JobStorage(settings).video_path(job_id))
    assert probed["duration"] == pytest.approx(45, abs=0.5)


def test_failed_prompt_keeps_timeline_length(client, worker, monkeypatch):
    """A failed prompt becomes black frames — the video must not get shorter."""
    import pytest

    project_id = client.post("/api/projects", json={"name": "Partial"}).json()["id"]
    csv = b'start,end,prompt\n0,4,"first scene"\n4,10,"second scene"\n'
    client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("timeline.csv", csv, "text/csv")},
    )

    original = worker.generator.generate

    def flaky(request):
        if "second scene" in request.prompt:
            raise RuntimeError("boom")
        return original(request)

    monkeypatch.setattr(worker.generator, "generate", flaky)

    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/jobs/{job_id}").json()
    assert (status["successful"], status["failed"]) == (1, 1)
    assert status["output"]["duration_seconds"] == 10
    assert status["output"]["frame_count"] == 1

    from app.config import get_settings

    probed = probe_video(JobStorage(get_settings()).video_path(job_id))
    assert probed["duration"] == pytest.approx(10, abs=0.4)

    # Retrying the failed prompt rebuilds the video with real footage.
    monkeypatch.setattr(worker.generator, "generate", original)
    assert client.post(f"/api/jobs/{job_id}/retry-failed").status_code == 202
    worker.run_once()

    final = client.get(f"/api/jobs/{job_id}").json()
    assert (final["successful"], final["failed"]) == (2, 0)
    assert final["output"]["frame_count"] == 2
    assert final["output"]["duration_seconds"] == 10


def test_all_prompts_failing_produces_no_video(client, worker, monkeypatch):
    project_id = create_project_with_csv(client, "All fail", 3)
    monkeypatch.setattr(worker.generator, "failure_rate", 1.0)

    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/jobs/{job_id}").json()
    assert status["status"] == JobStatus.COMPLETED
    assert status["failed"] == 3
    assert status["output"] is None


def test_job_items_carry_their_timeline_window(client, worker):
    project_id = create_project_with_csv(client, "Windows", 3, seconds_each=2)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    items = client.get(f"/api/jobs/{job_id}").json()["items"]

    assert [(i["start_seconds"], i["end_seconds"]) for i in items] == [(0, 2), (2, 4), (4, 6)]


def test_second_job_gets_its_own_id(client, worker):
    first = create_project_with_csv(client, "Batch one", 2)
    second = create_project_with_csv(client, "Batch two", 2)

    first_job = client.post(f"/api/projects/{first}/start").json()["job"]["job_id"]
    second_job = client.post(f"/api/projects/{second}/start").json()["job"]["job_id"]
    assert (first_job, second_job) == ("JOB-001", "JOB-002")

    worker.run_once()
    worker.run_once()

    history = client.get("/api/jobs").json()
    assert {job["job_id"] for job in history} == {"JOB-001", "JOB-002"}
    assert all(job["status"] == JobStatus.COMPLETED for job in history)


def test_cancel_stops_the_batch(client, worker):
    project_id = create_project_with_csv(client, "Cancelled", 5)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]

    worker.claim_next_job()
    with session_scope() as session:
        session.get(Job, job_id).cancel_requested = True
    worker.process_job(job_id)

    status = client.get(f"/api/jobs/{job_id}").json()
    assert status["status"] == JobStatus.CANCELLED
    assert status["completed"] == 0


def test_cannot_start_without_a_csv(client):
    project_id = client.post("/api/projects", json={"name": "No CSV"}).json()["id"]

    response = client.post(f"/api/projects/{project_id}/start")

    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


def test_invalid_csv_is_not_stored(client):
    project_id = client.post("/api/projects", json={"name": "Bad CSV"}).json()["id"]

    response = client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("bad.csv", b'start,end,prompt\n0,5,""\n', "text/csv")},
    )

    assert response.json()["valid"] is False
    assert client.get(f"/api/projects/{project_id}").json()["prompt_count"] == 0
    assert client.post(f"/api/projects/{project_id}/start").status_code == 400


def test_health_and_system_endpoints(client, settings):
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["generator"]["backend"] == "mock"

    system = client.get("/api/system").json()
    assert "comfyui" in system["available_backends"]
    assert "runware" in system["available_backends"]


def test_delete_job_removes_video_and_row(client, worker, settings):
    project_id = create_project_with_csv(client, "To delete", 2)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    storage = JobStorage(settings)
    assert storage.video_path(job_id).is_file()

    response = client.delete(f"/api/jobs/{job_id}")

    assert response.status_code == 204
    assert not storage.job_dir(job_id).exists()
    assert client.get(f"/api/jobs/{job_id}").status_code == 404
    assert client.get("/api/jobs").json() == []


def test_delete_refuses_while_running(client, worker):
    project_id = create_project_with_csv(client, "Still running", 2)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]

    response = client.delete(f"/api/jobs/{job_id}")

    assert response.status_code == 409
    assert "cancel it first" in response.json()["detail"]
    assert client.get(f"/api/jobs/{job_id}").status_code == 200


def test_delete_unknown_job_is_404(client):
    assert client.delete("/api/jobs/JOB-999").status_code == 404
