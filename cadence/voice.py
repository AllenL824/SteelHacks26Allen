"""ElevenLabs voice features. HARD RULE: only app.py may import this module —
nothing in cadence/'s core pipeline may depend on ElevenLabs, so if it's missing
or a key isn't set, the rest of the app is unaffected.

All audio is cached to disk (keyed by content hash) so the demo survives no Wi-Fi.
"""
import hashlib
import os

from dotenv import load_dotenv

from cadence import config

load_dotenv()

DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" — a stock ElevenLabs voice
TTS_MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"

_client = None


def available() -> bool:
    """True if an ElevenLabs key is configured (app uses this to show/hide voice UI)."""
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def client():
    global _client
    if _client is None:
        from elevenlabs.client import ElevenLabs
        _client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
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
    """Read the practice feedback aloud in a natural voice."""
    return _tts_to_file(text, DEFAULT_VOICE, tag="feedback")


def target_pace_audio(passage: str) -> str:
    """A smooth model reading of the passage — 'here's what fluent sounds like'."""
    return _tts_to_file(passage, DEFAULT_VOICE, tag="pace")


def clone_voice(sample_paths: list[str], name: str = "speakr-user") -> str:
    """Instant voice clone from the user's own recording(s). Returns a voice_id."""
    voice = client().voices.ivc.create(name=name, files=[open(p, "rb") for p in sample_paths])
    return voice.voice_id


def fluent_playback(passage: str, voice_id: str, tag: str = "clone") -> str:
    """The demo moment: the passage read fluently in the user's own cloned voice."""
    return _tts_to_file(passage, voice_id, tag=f"{tag}_{voice_id}")
