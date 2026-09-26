import pytest

from app.models import ItemStatus, JobItem
from app.services.audio_service import reflow_timeline
from app.services.storage import JobStorage
from app.services.video_service import build_scene_filter, transition_seconds_for
from app.tts import MockTextToSpeech, SpeechRequest, build_tts
from tests.conftest import probe_video

SMART_HEADER = (
    "start,end,prompt,transition,ken_burns,grade,grain,music,"
    "text_type,text_value,narration,voice\n"
)


def upload(client, name: str, rows: str) -> str:
    project_id = client.post("/api/projects", json={"name": name}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/upload-csv",
        files={"file": ("t.csv", (SMART_HEADER + rows).encode("utf-8"), "text/csv")},
    )
    assert response.json()["valid"] is True, response.json()["errors"]
    return project_id


# ----------------------------------------------------------------------- TTS


def test_mock_tts_writes_audio_of_plausible_length(settings, tmp_path):
    tts = MockTextToSpeech(words_per_second=3.5)
    target = tmp_path / "line.m4a"

    result = tts.synthesize(SpeechRequest(text=" ".join(["शब्द"] * 35), output_path=target))

    assert target.is_file()
    assert result.duration_seconds == pytest.approx(10.0, abs=0.5)
    assert result.backend == "mock"


def test_tts_backend_is_selectable(settings, monkeypatch):
    from app.config import get_settings

    assert build_tts(settings).name == "mock"
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    get_settings.cache_clear()
    assert build_tts(get_settings()).name == "sarvam"
    get_settings.cache_clear()


def test_unknown_tts_provider_is_rejected(settings, monkeypatch):
    monkeypatch.setattr(settings, "tts_provider", "nope")
    with pytest.raises(ValueError, match="Unknown TTS_PROVIDER"):
        build_tts(settings)


# ------------------------------------------------------------------- retiming


def test_reflow_stretches_scenes_to_their_narration():
    items = [
        JobItem(order_index=1, start_seconds=0, end_seconds=2, audio_seconds=4.0),
        JobItem(order_index=2, start_seconds=2, end_seconds=4, audio_seconds=1.5),
        JobItem(order_index=3, start_seconds=4, end_seconds=9, audio_seconds=None),
    ]

    total = reflow_timeline(items)

    assert (items[0].start_seconds, items[0].end_seconds) == (0.0, 4.0)
    assert (items[1].start_seconds, items[1].end_seconds) == (4.0, 5.5)
    # No narration on scene 3, so its authored 5s length is preserved.
    assert (items[2].start_seconds, items[2].end_seconds) == (5.5, 10.5)
    assert total == 10.5


def test_reflow_keeps_the_timeline_contiguous():
    items = [
        JobItem(order_index=i, start_seconds=0, end_seconds=1, audio_seconds=s)
        for i, s in enumerate([2.2, 3.7, 1.1, 5.9], start=1)
    ]

    reflow_timeline(items)

    for earlier, later in zip(items, items[1:]):
        assert earlier.end_seconds == later.start_seconds


# -------------------------------------------------------------- filter graph


def test_transition_seconds_defaults_and_cuts():
    assert transition_seconds_for(JobItem(transition=None)) == 0.0
    assert transition_seconds_for(JobItem(transition="cut")) == 0.0
    assert transition_seconds_for(JobItem(transition="dissolve")) == 0.5
    assert transition_seconds_for(JobItem(transition="dissolve", transition_seconds=0.8)) == 0.8


def test_scene_filter_includes_requested_effects(settings):
    item = JobItem(
        order_index=1, start_seconds=0, end_seconds=4,
        ken_burns="zoom_in", ken_burns_scale=1.2,
        grade="sepia", grain=20,
        text_type="date_stamp", text_value="14 अप्रैल, 1891",
    )

    chain = build_scene_filter(item, settings, 320, 180, 4.0)

    assert "zoompan" in chain
    assert "colorchannelmixer" in chain  # sepia
    assert "noise=alls=20" in chain
    assert "drawtext" in chain
    assert "Mukta" in chain  # font is now Mukta


def test_scene_filter_without_effects_is_a_plain_fit(settings):
    chain = build_scene_filter(JobItem(order_index=1), settings, 320, 180, 3.0)

    assert "zoompan" not in chain
    assert "drawtext" not in chain
    assert "scale=320:180" in chain


def test_drawtext_escapes_special_characters(settings):
    item = JobItem(order_index=1, text_type="lower_third", text_value="10:30 'quoted' 50%")

    chain = build_scene_filter(item, settings, 320, 180, 3.0)

    assert r"10\:30" in chain
    assert r"\'quoted\'" in chain
    assert r"50\%" in chain


# ------------------------------------------------------------- end to end


def test_render_with_effects_keeps_exact_duration(client, worker, settings):
    rows = (
        '0,3,"first scene",fadeblack,zoom_in,warm,light,,center_title,"शुरुआत",,\n'
        '3,6,"second scene",dissolve,pan_right,cold,medium,,,,,\n'
        '6,9,"third scene",dissolve:0.4,zoom_out,sepia,,,date_stamp,"1891",,\n'
    )
    project_id = upload(client, "Effects", rows)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/jobs/{job_id}").json()
    assert status["successful"] == 3
    assert status["output"]["duration_seconds"] == 9

    probed = probe_video(JobStorage(settings).video_path(job_id))
    # Transitions straddle their boundary, so the film must still be 9s.
    assert probed["duration"] == pytest.approx(9, abs=0.4)

    items = status["items"]
    assert items[0]["ken_burns"] == "zoom_in"
    assert items[1]["grade"] == "cold"
    assert items[2]["text_value"] == "1891"


def test_narration_retimes_the_film(client, worker, settings):
    """Authored timings are 2s each; narration is longer, so the film grows."""
    rows = (
        '0,2,"one",,,,,,,,"' + " ".join(["शब्द"] * 21) + '",\n'
        '2,4,"two",,,,,,,,"' + " ".join(["शब्द"] * 14) + '",\n'
    )
    project_id = upload(client, "Narrated", rows)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/jobs/{job_id}").json()
    items = status["items"]

    assert items[0]["audio_seconds"] == pytest.approx(6.0, abs=0.4)
    assert items[1]["audio_seconds"] == pytest.approx(4.0, abs=0.4)
    assert items[0]["end_seconds"] == items[1]["start_seconds"]
    assert status["output"]["duration_seconds"] == pytest.approx(10.0, abs=0.8)

    probed = probe_video(JobStorage(settings).video_path(job_id))
    assert probed["duration"] == pytest.approx(status["output"]["duration_seconds"], abs=0.5)


def test_fixed_timing_mode_keeps_authored_durations(client, worker, settings, monkeypatch):
    monkeypatch.setattr(settings, "timing_mode", "fixed")
    rows = '0,3,"one",,,,,,,,"' + " ".join(["शब्द"] * 35) + '",\n'
    project_id = upload(client, "Fixed", rows)
    job_id = client.post(f"/api/projects/{project_id}/start").json()["job"]["job_id"]
    worker.run_once()

    status = client.get(f"/api/jobs/{job_id}").json()

    assert status["output"]["duration_seconds"] == 3
    assert status["items"][0]["audio_seconds"] is not None


def test_system_endpoint_reports_tts(client):
    system = client.get("/api/system").json()

    assert system["tts_backend"] == "mock"
    assert set(system["available_tts_backends"]) >= {"mock", "sarvam", "elevenlabs"}
    assert system["tts"]["healthy"] is True
    assert system["timing_mode"] in {"audio", "fixed"}
