from cadence.align import AlignedWord
from cadence.enrich import build_enriched, voiced_fraction
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
    # both words fully covered by speech regions -> voiced_frac 1.00
    regions = [(0.0, 0.2), (1.4, 2.6)]
    text = build_enriched(words, aligned, flags, "the cat", regions)
    assert "caaat" in text
    assert "substituted" in text
    assert "mid_phrase_silence" in text
    assert "stretched_word" in text
    assert "gap_before=1.20" in text
    assert "the cat" in text  # passage included for context
    assert "voiced_frac=1.00" in text


def test_voiced_fraction_basic():
    # word spans 1.0s; only 0.2s of it overlaps a speech region -> 0.20 voiced
    w = Word("succeeded", 7.0, 9.0)  # 2.0s span
    regions = [(7.0, 7.4)]           # 0.4s voiced
    assert abs(voiced_fraction(w, regions) - 0.2) < 1e-6


def test_voiced_fraction_fully_voiced():
    w = Word("beyond", 10.0, 10.5)
    regions = [(9.8, 10.6)]
    assert voiced_fraction(w, regions) == 1.0


def test_voiced_fraction_zero_duration_defaults_to_one():
    w = Word("x", 5.0, 5.0)
    assert voiced_fraction(w, []) == 1.0


def test_block_word_shows_low_voiced_frac():
    # a swallowed block: 2.08s word, only 0.38s voiced -> ~0.18
    words = [Word("succeeded", 7.66, 9.74)]
    aligned = [AlignedWord("matched", 0, "succeeded", words[0])]
    flags = [Flag("stretched_word", 7.66, 9.74, 0, "took 2.08s")]
    regions = [(7.66, 8.04)]
    text = build_enriched(words, aligned, flags, "succeeded", regions)
    assert "voiced_frac=0.18" in text
