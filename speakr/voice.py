"""ElevenLabs voice features. HARD RULE: only app.py may import this module —
nothing in speakr/'s core pipeline may depend on ElevenLabs, so if it's missing
or a key isn't set, the rest of the app is unaffected.

TTS audio is cached to disk (keyed by content hash) so the demo survives no Wi-Fi.
Voice cloning uses the raw /v1/voices/add endpoint (the SDK's ivc.create is broken
in this version) and reuses a single voice slot so free-tier limits aren't hit.
"""
import hashlib
import json
import os

import requests
from dotenv import load_dotenv

from speakr import config

load_dotenv()

DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" — a stock ElevenLabs voice
TTS_MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
API = "https://api.elevenlabs.io/v1"

_client = None
# Keep at most ONE cloned voice alive (free tier has ~3 slots); reuse it.
_last_clone: dict[str, str | None] = {"key": None, "voice_id": None}


def available() -> bool:
    """True if an ElevenLabs key is configured (app uses this to show/hide voice UI)."""
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def _key() -> str:
    return os.environ["ELEVENLABS_API_KEY"]


def client():
    global _client
    if _client is None:
        from elevenlabs.client import ElevenLabs
        _client = ElevenLabs(api_key=_key())
    return _client


def _tts_to_file(text: str, voice_id: str, tag: str) -> str:
    """Text-to-speech -> cached mp3 path. Cache key covers text + voice + model."""
    key = hashlib.sha256(f"{tag}|{voice_id}|{TTS_MODEL}|{text}".encode()).hexdigest()[:20]
    out = config.CACHE_DIR / f"voice_{key}.mp3"
    if not out.exists():
        audio = client().text_to_speech.convert(
            voice_id=voice_id, text=text,
            model_id=TTS_MODEL, output_format=OUTPUT_FORMAT,
        )
        out.write_bytes(b"".join(audio))  # convert() yields byte chunks
    return str(out)


def speak_feedback(text: str) -> str:
    """Read the practice feedback / spoken coach debrief aloud in a natural voice."""
    return _tts_to_file(text, DEFAULT_VOICE, tag="feedback")


def target_pace_audio(passage: str) -> str:
    """A smooth model reading of the passage — 'here's what fluent sounds like'."""
    return _tts_to_file(passage, DEFAULT_VOICE, tag="pace")


def _delete_voice(voice_id: str) -> None:
    requests.delete(f"{API}/voices/{voice_id}", headers={"xi-api-key": _key()}, timeout=30)


def clone_voice(sample_paths: list[str], name: str = "speakr-user") -> str:
    """Instant voice clone from the user's own recording(s). Reuses a single slot:
    the same sample returns the same voice; a new sample frees the old slot first."""
    ck = "|".join(sample_paths)
    if _last_clone["key"] == ck and _last_clone["voice_id"]:
        return _last_clone["voice_id"]
    if _last_clone["voice_id"]:  # free the previous slot before making a new one
        try:
            _delete_voice(_last_clone["voice_id"])
        except Exception:
            pass
    files = [("files", (os.path.basename(p), open(p, "rb"), "audio/wav")) for p in sample_paths]
    resp = requests.post(
        f"{API}/voices/add", headers={"xi-api-key": _key()},
        data={"name": name, "labels": json.dumps({})}, files=files, timeout=60,
    )
    resp.raise_for_status()
    voice_id = resp.json()["voice_id"]
    _last_clone.update(key=ck, voice_id=voice_id)
    return voice_id


def fluent_playback(passage: str, voice_id: str, tag: str = "clone") -> str:
    """The demo moment: the passage read fluently in the user's own cloned voice."""
    return _tts_to_file(passage, voice_id, tag=f"{tag}_{voice_id}")
