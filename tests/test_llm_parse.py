from cadence.llm import parse_events, strip_fences


def test_strip_fences():
    assert strip_fences('```json\n[{"a": 1}]\n```') == '[{"a": 1}]'
    assert strip_fences('[{"a": 1}]') == '[{"a": 1}]'


def test_parse_valid_events():
    raw = """```json
    [{"word": "cat", "start": 1.4, "type": "prolongation",
      "confidence": 0.9, "evidence": "duration 1.2s vs expected 0.22s"}]
    ```"""
    events = parse_events(raw)
    assert len(events) == 1
    assert events[0].type == "prolongation"
    assert events[0].start == 1.4


def test_parse_garbage_returns_empty():
    assert parse_events("I could not decide.") == []


def test_parse_drops_invalid_items_keeps_valid():
    raw = ('[{"word": "cat", "start": 1.4, "type": "prolongation", '
           '"confidence": 0.9, "evidence": "x"}, {"type": "nonsense"}]')
    events = parse_events(raw)
    assert len(events) == 1
