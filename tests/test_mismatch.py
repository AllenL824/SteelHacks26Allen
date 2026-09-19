from cadence.mismatch import expected_duration, find_flags, syllable_count
from cadence.transcribe import Word
from cadence.align import AlignedWord


def test_syllable_count():
    assert syllable_count("cat") == 1
    assert syllable_count("rainbow") == 2
    assert syllable_count("beautiful") >= 3
    assert syllable_count("") == 1  # floor: never zero


def test_expected_duration_has_floor():
    assert expected_duration("a") >= 0.15


def _aligned(words: list[Word]) -> list[AlignedWord]:
    return [AlignedWord("matched", i, w.text, w) for i, w in enumerate(words)]


def test_stretched_word_flagged():
    words = [
        Word("the", 0.0, 0.2),
        Word("cat", 0.3, 1.5),   # 1.2s for one syllable -> stretched
    ]
    flags = find_flags(words, [(0.0, 1.5)], _aligned(words))
    kinds = [f.kind for f in flags]
    assert "stretched_word" in kinds
    stretched = next(f for f in flags if f.kind == "stretched_word")
    assert stretched.word_index == 1


def test_mid_phrase_silence_flagged():
    words = [
        Word("the", 0.0, 0.2),
        Word("cat", 1.4, 1.7),   # 1.2s gap, previous word has no sentence-ending punct
    ]
    flags = find_flags(words, [(0.0, 0.2), (1.4, 1.7)], _aligned(words))
    assert any(f.kind == "mid_phrase_silence" and f.word_index == 1 for f in flags)


def test_gap_after_sentence_end_not_flagged():
    words = [
        Word("end.", 0.0, 0.3),
        Word("Next", 1.5, 1.8),
    ]
    flags = find_flags(words, [(0.0, 0.3), (1.5, 1.8)], _aligned(words))
    assert not any(f.kind == "mid_phrase_silence" for f in flags)


def test_unexplained_sound_flagged():
    words = [Word("the", 0.0, 0.2), Word("cat", 2.0, 2.3)]
    # middle region has no overlapping word -> likely dropped filler/repetition
    flags = find_flags(words, [(0.0, 0.2), (0.9, 1.4), (2.0, 2.3)], _aligned(words))
    unexplained = [f for f in flags if f.kind == "unexplained_sound"]
    assert len(unexplained) == 1
    assert abs(unexplained[0].start - 0.9) < 0.01


def test_clean_read_no_flags():
    words = [Word("the", 0.0, 0.2), Word("cat", 0.3, 0.55)]
    flags = find_flags(words, [(0.0, 0.55)], _aligned(words))
    assert flags == []
