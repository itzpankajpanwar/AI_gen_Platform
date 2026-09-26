import shutil
import subprocess

from app.tts.base import SpeechRequest, SpeechResult, SynthesisError, TextToSpeech, VoiceHealth

# Hindi narration sits around this rate; used to fake a believable clip length.
WORDS_PER_SECOND = 3.5
MIN_SECONDS = 0.6


class MockTextToSpeech(TextToSpeech):
    """Writes silent audio of a realistic length instead of calling a provider.

    Lets the whole narration path — per-scene synthesis, duration measurement,
    audio-driven re-timing, mixing — be built and tested with no API key and no
    spend. Swap in a real backend and nothing downstream changes.
    """

    name = "mock"

    def __init__(self, ffmpeg_binary: str = "ffmpeg", words_per_second: float = WORDS_PER_SECOND):
        self.ffmpeg_binary = ffmpeg_binary
        self.words_per_second = words_per_second or WORDS_PER_SECOND

    def estimate_seconds(self, text: str) -> float:
        words = len(text.split())
        return max(words / self.words_per_second, MIN_SECONDS)

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        binary = shutil.which(self.ffmpeg_binary)
        if binary is None:
            raise SynthesisError(f"ffmpeg not found (looked for '{self.ffmpeg_binary}')")

        pace = request.pace or 1.0
        seconds = round(self.estimate_seconds(request.text) / pace, 3)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        command = [
            binary, "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=channel_layout=mono:sample_rate=44100",
            "-t", f"{seconds:.3f}",
            "-c:a", "aac", "-b:a", "96k",
            str(request.output_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if completed.returncode != 0 or not request.output_path.is_file():
            tail = (completed.stderr or "").strip().splitlines()[-4:]
            raise SynthesisError("mock TTS could not write audio: " + " | ".join(tail))

        return SpeechResult(
            output_path=request.output_path,
            duration_seconds=seconds,
            backend=self.name,
            voice=request.voice or "mock-voice",
            metadata={"simulated": True, "words": len(request.text.split())},
        )

    def health_check(self) -> VoiceHealth:
        available = shutil.which(self.ffmpeg_binary) is not None
        return VoiceHealth(
            healthy=available,
            backend=self.name,
            detail=(
                "Mock narration (silent audio of realistic length)"
                if available
                else f"ffmpeg not found (looked for '{self.ffmpeg_binary}')"
            ),
            info={"words_per_second": self.words_per_second},
        )
