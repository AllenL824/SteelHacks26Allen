"""Rules-only classifier: the comparison point that shows what Nemotron adds."""
from cadence.align import AlignedWord
from cadence.llm import Event
from cadence.mismatch import Flag
from cadence.transcribe import Word, normalize

FLAG_TO_TYPE = {
    "stretched_word": "prolongation",
    "mid_phrase_silence": "block",
    "unexplained_sound": "filler",
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
    # inserted word identical to a neighbor -> word_repetition
    for i, a in enumerate(aligned):
        if a.status != "inserted" or a.word is None:
            continue
        neighbors = [aligned[j] for j in (i - 1, i + 1) if 0 <= j < len(aligned)]
        for nb in neighbors:
            if nb.word is not None and normalize(nb.word.text) == normalize(a.word.text):
                events.append(Event(
                    word=a.word.text, start=a.word.start, type="word_repetition",
                    confidence=0.5, evidence="rule: inserted word repeats neighbor",
                ))
                break
    return sorted(events, key=lambda e: e.start)
