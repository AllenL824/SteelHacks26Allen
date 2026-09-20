from speakr.llm import Event
from eval.run_eval import match_events


def ev(t, start):
    return Event(word="x", start=start, type=t, confidence=0.9, evidence="")


def test_match_same_type_within_tolerance():
    labels = [{"type": "block", "start": 1.0, "end": 2.0}]
    tp, fp, fn = match_events([ev("block", 1.2)], labels)
    assert (len(tp), len(fp), len(fn)) == (1, 0, 0)


def test_wrong_type_is_fp_and_fn():
    labels = [{"type": "block", "start": 1.0, "end": 2.0}]
    tp, fp, fn = match_events([ev("prolongation", 1.2)], labels)
    assert (len(tp), len(fp), len(fn)) == (0, 1, 1)


def test_too_far_in_time_is_fp():
    labels = [{"type": "block", "start": 1.0, "end": 1.5}]
    tp, fp, fn = match_events([ev("block", 5.0)], labels)
    assert (len(tp), len(fp), len(fn)) == (0, 1, 1)


def test_each_label_matched_once():
    labels = [{"type": "block", "start": 1.0, "end": 2.0}]
    tp, fp, fn = match_events([ev("block", 1.1), ev("block", 1.3)], labels)
    assert (len(tp), len(fp)) == (1, 1)
