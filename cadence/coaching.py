"""Targeted practice recommendations.

Rules measure which sound the reader struggles with (from the disfluent words);
curated content is selected to match. Consistent with the project's split:
the pipeline measures, and the content/narration layer interprets.
"""
from dataclasses import dataclass

from cadence import coaching_content
from cadence.llm import Event
from cadence.transcribe import normalize

# Disfluency types whose onset sound is meaningful (fillers/false alarms excluded).
_DISFLUENCY = {"block", "prolongation", "sound_repetition", "word_repetition"}
_DIGRAPHS = ("th", "sh", "ch", "wh", "ph")
_VOWELS = "aeiou"


def leading_sound(word: str) -> str | None:
    """The leading consonant sound of a word: a digraph (th/sh/ch/wh/ph) if present,
    else the first consonant letter. None for vowel-initial or empty words."""
    w = normalize(word)
    if not w or w[0] in _VOWELS:
        return None
    for d in _DIGRAPHS:
        if w.startswith(d):
            return d
    return w[0]


def problem_sounds(events: list[Event]) -> list[tuple[str, int]]:
    """Ranked (sound, count) of the sounds the reader stumbled on, most first."""
    counts: dict[str, int] = {}
    for e in events:
        if e.type not in _DISFLUENCY:
            continue
        s = leading_sound(e.word)
        if s is None:
            continue
        counts[s] = counts.get(s, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


@dataclass
class Recommendation:
    problem_sound: str | None
    sound_count: int
    tongue_twister: str
    breathing: str
    suggested_passage: str | None


def recommend(events: list[Event], metrics: dict) -> Recommendation:
    ranked = problem_sounds(events)
    sound, count = ranked[0] if ranked else (None, 0)
    return Recommendation(
        problem_sound=sound,
        sound_count=count,
        tongue_twister=coaching_content.pick_tongue_twister(sound),
        breathing=coaching_content.pick_breathing(),
        suggested_passage=coaching_content.suggest_passage(sound),
    )
