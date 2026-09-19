from cadence.align import align
from cadence.transcribe import Word


def w(text: str, i: int) -> Word:
    return Word(text=text, start=float(i), end=float(i) + 0.3)


def statuses(result):
    return [a.status for a in result]


def test_perfect_read_all_matched():
    words = [w(t, i) for i, t in enumerate(["the", "quick", "brown", "fox"])]
    result = align(words, "The quick brown fox")
    assert statuses(result) == ["matched"] * 4
    assert [a.passage_index for a in result] == [0, 1, 2, 3]


def test_repeated_word_is_inserted():
    words = [w(t, i) for i, t in enumerate(["the", "the", "quick", "fox"])]
    result = align(words, "The quick fox")
    assert statuses(result).count("inserted") == 1
    assert statuses(result).count("matched") == 3


def test_skipped_word():
    words = [w(t, i) for i, t in enumerate(["the", "fox"])]
    result = align(words, "The quick fox")
    skipped = [a for a in result if a.status == "skipped"]
    assert len(skipped) == 1
    assert skipped[0].passage_word == "quick"
    assert skipped[0].word is None


def test_substitution():
    words = [w(t, i) for i, t in enumerate(["the", "slow", "fox"])]
    result = align(words, "The quick fox")
    subs = [a for a in result if a.status == "substituted"]
    assert len(subs) == 1
    assert subs[0].passage_word == "quick"
    assert subs[0].word.text == "slow"


def test_punctuation_and_case_ignored():
    words = [w("Fox,", 0)]
    result = align(words, "fox")
    assert statuses(result) == ["matched"]
