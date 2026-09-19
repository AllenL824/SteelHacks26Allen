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


def test_repetition_flag_maps_to_word_repetition():
    # repetition detection now lives in mismatch.find_flags; the baseline just maps
    # the resulting flag to word_repetition (the judge distinguishes word vs sound).
    words = [Word("the", 0.0, 0.2), Word("the", 0.3, 0.5)]
    flags = [Flag("repetition", 0.0, 0.5, 0, "'the' repeated 2x")]
    events = classify(flags, [], words)
    assert len(events) == 1
    assert events[0].type == "word_repetition"
