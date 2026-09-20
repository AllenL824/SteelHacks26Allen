"""Rules-only classifier: the comparison point that shows what Nemotron adds."""
from speakr.align import AlignedWord
from speakr.llm import Event
from speakr.mismatch import Flag
from speakr.transcribe import Word

FLAG_TO_TYPE = {
    "stretched_word": "prolongation",
    "mid_phrase_silence": "block",
    "unexplained_sound": "filler",
    "repetition": "word_repetition",  # rules can't tell word vs sound repetition; the judge can
}


def classify(
    flags: list[Flag],
    aligned: list[AlignedWord],
    words: list[Word],
) -> list[Event]:
    events: list[Event] = []
    for f in flags:
        word = words[f.word_index].text if f.word_index is not None else "(sound)"
        events.append(Event(
            word=word, start=f.start, type=FLAG_TO_TYPE[f.kind],
            confidence=0.5, evidence=f"rule: {f.kind}",
        ))
    return sorted(events, key=lambda e: e.start)
