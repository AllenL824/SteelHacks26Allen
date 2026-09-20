import hashlib
import json
from dataclasses import asdict, dataclass
from functools import lru_cache

from faster_whisper import WhisperModel

from speakr import config


@dataclass
class Word:
    text: str      # original token, punctuation kept (mismatch.py needs it)
    start: float
    end: float


def normalize(text: str) -> str:
    return "".join(c for c in text.lower() if c.isalnum() or c == "'")


@lru_cache(maxsize=1)
def _model() -> WhisperModel:
    return WhisperModel(config.WHISPER_MODEL, compute_type=config.WHISPER_COMPUTE)


def _file_key(audio_path: str) -> str:
    """Content hash of the audio file — same audio → same key across processes."""
    h = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    h.update(f"|{config.WHISPER_MODEL}|{config.FILLER_PROMPT}".encode())
    return h.hexdigest()


@lru_cache(maxsize=None)
def transcribe(audio_path: str) -> list[Word]:
    """Transcribe with word timestamps. Cached to disk by audio-content hash so
    the *same* words are returned every run — Whisper's timings vary slightly
    run-to-run, and that instability would otherwise change the downstream judge
    cache key and force a fresh (slow) API call each time."""
    cache_path = config.CACHE_DIR / f"asr_{_file_key(audio_path)}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
        return [Word(**w) for w in data]

    segments, _ = _model().transcribe(
        audio_path,
        word_timestamps=True,
        initial_prompt=config.FILLER_PROMPT,
        condition_on_previous_text=config.WHISPER_CONDITION_ON_PREVIOUS,
    )
    words: list[Word] = []
    for seg in segments:
        for w in seg.words or []:
            words.append(Word(text=w.word.strip(), start=w.start, end=w.end))
    cache_path.write_text(json.dumps([asdict(w) for w in words]))
    return words
