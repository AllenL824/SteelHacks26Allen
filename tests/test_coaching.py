from speakr import coaching_content
from speakr.coaching import Recommendation, leading_sound, problem_sounds, recommend
from speakr.llm import Event


def ev(word: str, typ: str) -> Event:
    return Event(word=word, start=0.0, type=typ, confidence=0.9, evidence="")


def test_leading_sound_single_consonant():
    assert leading_sound("strikes") == "s"
    assert leading_sound("sun") == "s"
    assert leading_sound("came") == "c"
    assert leading_sound("beautiful") == "b"


def test_leading_sound_digraph():
    assert leading_sound("they") == "th"
    assert leading_sound("ship") == "sh"
    assert leading_sound("cheese") == "ch"


def test_leading_sound_vowel_or_empty_is_none():
    assert leading_sound("apple") is None
    assert leading_sound("") is None
    assert leading_sound("-") is None


def test_problem_sounds_ranks_and_ignores_non_disfluencies():
    events = [
        ev("strikes", "block"),
        ev("sun", "prolongation"),
        ev("stronger", "sound_repetition"),
        ev("form", "block"),
        ev("umm", "filler"),          # ignored
        ev("nothing", "false_alarm"),  # ignored
    ]
    ps = problem_sounds(events)
    assert ps[0] == ("s", 3)          # strikes, sun, stronger
    assert ("f", 1) in ps


def test_problem_sounds_empty():
    assert problem_sounds([]) == []
    assert problem_sounds([ev("umm", "filler")]) == []


def test_recommend_targets_top_sound():
    events = [ev("strikes", "block"), ev("sun", "prolongation"), ev("stronger", "block")]
    rec = recommend(events, {"wpm": 150})
    assert isinstance(rec, Recommendation)
    assert rec.problem_sound == "s"
    assert rec.sound_count == 3
    assert rec.tongue_twister == coaching_content.TONGUE_TWISTERS["s"][0]
    assert rec.breathing
    assert rec.suggested_passage == "sea_shore"


def test_recommend_no_disfluencies_uses_general_fallback():
    rec = recommend([], {"wpm": 150})
    assert rec.problem_sound is None
    assert rec.sound_count == 0
    assert rec.tongue_twister in coaching_content.GENERAL_TWISTERS
    assert rec.breathing
    assert rec.suggested_passage is None


def test_recommend_unknown_sound_falls_back_to_general_twister():
    # a sound we have no curated twister for still yields a general one, no crash
    rec = recommend([ev("xylophone", "block")], {"wpm": 150})
    assert rec.problem_sound == "x"
    assert rec.tongue_twister  # non-empty (general fallback)
