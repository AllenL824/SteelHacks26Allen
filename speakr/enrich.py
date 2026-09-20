from speakr.align import AlignedWord
from speakr.mismatch import Flag, expected_duration
from speakr.transcribe import Word


def voiced_fraction(word: Word, regions: list[tuple[float, float]]) -> float:
    """Fraction of a word's span covered by VAD speech regions (0-1).

    A low value means most of the word's duration is silence — e.g. a block
    (silent stuck moment) that the transcriber attached to the neighbouring word.
    Zero-duration words default to 1.0 (no signal to interpret).
    """
    dur = word.end - word.start
    if dur <= 0:
        return 1.0
    voiced = sum(
        max(0.0, min(word.end, e) - max(word.start, s)) for s, e in regions
    )
    return max(0.0, min(1.0, voiced / dur))


def build_enriched(
    words: list[Word],
    aligned: list[AlignedWord],
    flags: list[Flag],
    passage: str,
    regions: list[tuple[float, float]],
) -> str:
    status_by_word_id = {id(a.word): a.status for a in aligned if a.word is not None}
    flags_by_index: dict[int, list[str]] = {}
    for f in flags:
        if f.word_index is not None:
            flags_by_index.setdefault(f.word_index, []).append(f.kind)

    lines = [
        f"PASSAGE: {passage}",
        "",
        "TRANSCRIPT (one word per line). voiced_frac is the fraction of the word's "
        "duration that contains actual voice (from VAD); the rest is silence.",
    ]
    prev_end: float | None = None
    for i, w in enumerate(words):
        gap = (w.start - prev_end) if prev_end is not None else 0.0
        prev_end = w.end
        dur = w.end - w.start
        exp = expected_duration(w.text)
        vf = voiced_fraction(w, regions)
        status = status_by_word_id.get(id(w), "matched")
        wflags = ",".join(flags_by_index.get(i, [])) or "none"
        lines.append(
            f"[{i}] word={w.text!r} start={w.start:.2f} end={w.end:.2f} "
            f"dur={dur:.2f} expected={exp:.2f} voiced_frac={vf:.2f} gap_before={gap:.2f} "
            f"status={status} flags={wflags}"
        )

    skipped = [a.passage_word for a in aligned if a.status == "skipped"]
    if skipped:
        lines += ["", f"SKIPPED PASSAGE WORDS: {', '.join(skipped)}"]

    region_flags = [f for f in flags if f.word_index is None]
    if region_flags:
        lines += ["", "UNEXPLAINED SPEECH REGIONS (sound but no transcribed word):"]
        for f in region_flags:
            lines.append(f"  {f.start:.2f}-{f.end:.2f}s: {f.detail}")

    return "\n".join(lines)
