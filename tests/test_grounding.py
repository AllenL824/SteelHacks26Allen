from speakr.llm import grounded


def test_feedback_with_known_numbers_passes():
    metrics = {"wpm": 142, "accuracy_pct": 91, "long_pauses": 2, "speech_seconds": 18.5}
    assert grounded("You read at 142 WPM with 2 long pauses.", metrics)


def test_feedback_with_invented_number_fails():
    metrics = {"wpm": 142, "accuracy_pct": 91, "long_pauses": 2, "speech_seconds": 18.5}
    assert not grounded("You paused 7 times.", metrics)


def test_feedback_without_numbers_passes():
    assert grounded("Nice steady pace. Try the pausing drill.", {"wpm": 100})
