"""Hosted narration backends.

Both are wired against their documented HTTP APIs but unverified against a live
account — no key existed when they were written. Treat the request shapes as a
starting point and check the response parsing on first real call.
"""

import base64
import shutil
import subprocess

import httpx

from app.tts.base import SpeechRequest, SpeechResult, SynthesisError, TextToSpeech, VoiceHealth


def probe_duration(path, ffprobe_binary: str = "ffprobe") -> float:
    """Read a rendered clip's real length. This is what re-times the timeline."""
    binary = shutil.which(ffprobe_binary)
    if binary is None:
        raise SynthesisError(f"ffprobe not found (looked for '{ffprobe_binary}')")
    completed = subprocess.run(
        [binary, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return round(float(completed.stdout.strip()), 3)
    except ValueError as exc:
        raise SynthesisError(f"could not read duration of {path}: {completed.stderr[:200]}") from exc


class SarvamTextToSpeech(TextToSpeech):
    """Sarvam AI — Indian-language TTS (Bulbul)."""

    name = "sarvam"

    def __init__(
        self,
        api_key: str,
        model: str = "bulbul:v2",
        base_url: str = "https://api.sarvam.ai",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout_seconds)

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        if not self.api_key:
            raise SynthesisError("SARVAM_API_KEY is not set")

        payload = {
            "inputs": [request.text],
            "target_language_code": request.language or "hi-IN",
            "speaker": request.voice or None,
            "model": request.model or self.model,
            "pace": request.pace,
            "pitch": request.pitch,
            "loudness": request.loudness,
        }
        payload = {key: value for key, value in payload.items() if value is not None}

        try:
            response = self._client.post(
                f"{self.base_url}/text-to-speech",
                json=payload,
                headers={"api-subscription-key": self.api_key, "Content-Type": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise SynthesisError(f"Cannot reach Sarvam: {exc}") from exc
        if response.status_code >= 400:
            raise SynthesisError(f"Sarvam rejected the request: {response.text[:500]}")

        body = response.json()
        audios = body.get("audios") or []
        if not audios:
            raise SynthesisError(f"Sarvam returned no audio: {str(body)[:300]}")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        request.output_path.write_bytes(base64.b64decode(audios[0]))

        return SpeechResult(
            output_path=request.output_path,
            duration_seconds=probe_duration(request.output_path),
            backend=self.name,
            voice=request.voice,
            metadata={"model": request.model or self.model},
        )

    def health_check(self) -> VoiceHealth:
        if not self.api_key:
            return VoiceHealth(False, self.name, "SARVAM_API_KEY is not set", {"model": self.model})
        # No live call: every Sarvam request is billable.
        return VoiceHealth(
            True, self.name, "API key configured (verified on first synthesis)",
            {"model": self.model, "base_url": self.base_url},
        )

    def close(self) -> None:
        self._client.close()


class ElevenLabsTextToSpeech(TextToSpeech):
    """ElevenLabs — multilingual TTS."""

    name = "elevenlabs"

    def __init__(
        self,
        api_key: str,
        model: str = "eleven_multilingual_v2",
        base_url: str = "https://api.elevenlabs.io/v1",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout_seconds)

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        if not self.api_key:
            raise SynthesisError("ELEVENLABS_API_KEY is not set")
        if not request.voice:
            raise SynthesisError("ElevenLabs needs a voice id (set TTS_VOICE or the voice column)")

        try:
            response = self._client.post(
                f"{self.base_url}/text-to-speech/{request.voice}",
                json={
                    "text": request.text,
                    "model_id": request.model or self.model,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise SynthesisError(f"Cannot reach ElevenLabs: {exc}") from exc
        if response.status_code >= 400:
            raise SynthesisError(f"ElevenLabs rejected the request: {response.text[:500]}")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        request.output_path.write_bytes(response.content)

        return SpeechResult(
            output_path=request.output_path,
            duration_seconds=probe_duration(request.output_path),
            backend=self.name,
            voice=request.voice,
            metadata={"model": request.model or self.model},
        )

    def health_check(self) -> VoiceHealth:
        if not self.api_key:
            return VoiceHealth(False, self.name, "ELEVENLABS_API_KEY is not set", {})
        return VoiceHealth(
            True, self.name, "API key configured (verified on first synthesis)",
            {"model": self.model},
        )

    def close(self) -> None:
        self._client.close()
