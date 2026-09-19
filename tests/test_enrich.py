from cadence.align import AlignedWord
from cadence.enrich import build_enriched
from cadence.mismatch import Flag
from cadence.transcribe import Word


def test_enriched_contains_timing_status_and_flags():
    words = [Word("the", 0.0, 0.2), Word("caaat", 1.4, 2.6)]
    aligned = [
        AlignedWord("matched", 0, "the", words[0]),
        AlignedWord("substituted", 1, "cat", words[1]),
    ]
    flags = [
        Flag("mid_phrase_silence", 0.2, 1.4, 1, "1.20s silence before 'caaat'"),
        Flag("stretched_word", 1.4, 2.6, 1, "'caaat' took 1.20s, expected ~0.22s"),
    ]
    text = build_enriched(words, aligned, flags, passage="the cat")
    assert "caaat" in text
    assert "substituted" in text
    assert "mid_phrase_silence" in text
    assert "stretched_word" in text
    assert "gap_before=1.20" in text
    assert "the cat" in text  # passage included for context
