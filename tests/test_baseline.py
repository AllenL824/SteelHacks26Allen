from cadence.align import AlignedWord
from cadence.baseline import classify
from cadence.mismatch import Flag
from cadence.transcribe import Word


def test_rules_map_flags_to_events():
    flags = [
        Flag("stretched_word", 1.0, 2.0, 1, ""),
        Flag("mid_phrase_silence", 3.0, 4.0, 2, ""),
        Flag("unexplained_sound", 5.0, 5.4, None, ""),
    ]
    words = [Word("a", 0.0, 0.1), Word("b", 1.0, 2.0), Word("c", 3.0, 4.0)]
    events = classify(flags, [], words)
    types = [e.type for e in events]
    assert types == ["prolongation", "block", "filler"]
    assert events[0].start == 1.0


def test_repeated_inserted_word_is_word_repetition():
    the1, the2 = Word("the", 0.0, 0.2), Word("the", 0.3, 0.5)
    aligned = [
        AlignedWord("inserted", None, None, the1),
        AlignedWord("matched", 0, "the", the2),
    ]
    events = classify([], aligned, [the1, the2])
    assert len(events) == 1
    assert events[0].type == "word_repetition"
