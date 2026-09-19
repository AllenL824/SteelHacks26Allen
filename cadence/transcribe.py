from dataclasses import dataclass
from functools import lru_cache

from faster_whisper import WhisperModel

from cadence import config


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


@lru_cache(maxsize=None)
def transcribe(audio_path: str) -> list[Word]:
    segments, _ = _model().transcribe(
        audio_path,
        word_timestamps=True,
        initial_prompt=config.FILLER_PROMPT,
    )
    words: list[Word] = []
    for seg in segments:
        for w in seg.words or []:
            words.append(Word(text=w.word.strip(), start=w.start, end=w.end))
    return words
