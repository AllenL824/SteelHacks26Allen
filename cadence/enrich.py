from cadence.align import AlignedWord
from cadence.mismatch import Flag, expected_duration
from cadence.transcribe import Word


def build_enriched(
    words: list[Word],
    aligned: list[AlignedWord],
    flags: list[Flag],
    passage: str,
) -> str:
    status_by_word_id = {id(a.word): a.status for a in aligned if a.word is not None}
    flags_by_index: dict[int, list[str]] = {}
    for f in flags:
        if f.word_index is not None:
            flags_by_index.setdefault(f.word_index, []).append(f.kind)

    lines = [f"PASSAGE: {passage}", "", "TRANSCRIPT (one word per line):"]
    prev_end: float | None = None
    for i, w in enumerate(words):
        gap = (w.start - prev_end) if prev_end is not None else 0.0
        prev_end = w.end
        dur = w.end - w.start
        exp = expected_duration(w.text)
        status = status_by_word_id.get(id(w), "matched")
        wflags = ",".join(flags_by_index.get(i, [])) or "none"
        lines.append(
            f"[{i}] word={w.text!r} start={w.start:.2f} end={w.end:.2f} "
            f"dur={dur:.2f} expected={exp:.2f} gap_before={gap:.2f} "
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
