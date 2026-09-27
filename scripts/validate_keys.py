#!/usr/bin/env python3
"""Quick pre-flight: confirm the OpenAI + Sarvam keys in .env actually work."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import get_settings

s = get_settings()
tmp = Path("/tmp")

# Sarvam TTS
try:
    from app.tts.providers import SarvamTextToSpeech
    from app.tts.base import SpeechRequest
    tts = SarvamTextToSpeech(api_key=s.sarvam_api_key, model=s.sarvam_model,
                             speaker=s.sarvam_speaker, sample_rate=s.sarvam_sample_rate,
                             base_url=s.sarvam_base_url, timeout_seconds=60)
    r = tts.synthesize(SpeechRequest(text="नमस्ते, यह एक परीक्षण है।", output_path=tmp / "kv.m4a",
                       voice=s.sarvam_speaker, language="hi-IN", model=s.sarvam_model, pace=1.15))
    print(f"SARVAM: OK ({r.duration_seconds:.1f}s clip)")
except Exception as e:
    print(f"SARVAM: FAIL {type(e).__name__}: {str(e)[:160]}")

# OpenAI image
try:
    from app.generators.api_backends import OpenAIImageGenerator
    from app.generators.base import GenerationRequest
    g = OpenAIImageGenerator(api_key=s.openai_api_key, model=s.openai_image_model,
                             size=s.openai_image_size, quality=s.openai_image_quality,
                             base_url=s.openai_base_url, timeout_seconds=120)
    g.generate(GenerationRequest(prompt="a plain grey stone on a white background, studio photo",
               output_path=tmp / "kv.png", width=1280, height=720, steps=1, seed=0, image_format="png"))
    print("OPENAI: OK (1 image generated)")
except Exception as e:
    print(f"OPENAI: FAIL {type(e).__name__}: {str(e)[:160]}")
