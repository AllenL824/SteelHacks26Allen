import hashlib
import json
import os
import re
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from cadence import config

load_dotenv()

EventType = Literal[
    "sound_repetition", "word_repetition", "prolongation",
    "block", "filler", "false_alarm",
]


class Event(BaseModel):
    word: str
    start: float
    type: EventType
    confidence: float
    evidence: str


JUDGE_SYSTEM = """detailed thinking off
You classify moments in a read-aloud recording where the audio and transcript don't line up.
You are given a passage and an enriched transcript with per-word timing, alignment status, and rule-based flags.
For EACH flagged moment decide what it was:
- sound_repetition: a sound/syllable repeated (k-k-cat)
- word_repetition: a whole word repeated
- prolongation: a sound stretched out (caaaat)
- block: a silent stuck moment mid-phrase
- filler: um/uh/like inserted
- false_alarm: the flag is explainable (transcription error, natural pause, reading style)
A 'repetition' flag (or the transcript showing the same word twice in a row, or a cut-off fragment like 's-' or 'th-' before a word) means the reader repeated something. Classify it as word_repetition when a whole word recurs, or sound_repetition when only a sound/syllable or fragment recurs. Prefer this over prolongation whenever the same word or sound recurs.
A 'stretched_word' flag only means the word's total duration is long. Use voiced_frac to decide what it actually was:
- LOW voiced_frac (roughly < 0.5): most of the word's span is SILENCE, not voice. The transcriber attached a silent pause to this word -> classify as block, not prolongation.
- HIGH voiced_frac (roughly > 0.8) AND much longer than expected: a genuinely held sound -> prolongation.
- HIGH voiced_frac but only mildly longer than expected: a naturally long word read fluently -> false_alarm.
For alignment mismatches (substituted/inserted/skipped) decide: transcription error -> false_alarm; speaker misread -> the fitting type.
Never diagnose. Only classify moments using the evidence given.
Reply with ONLY a JSON array, one object per flagged moment:
[{"word": str, "start": float, "type": str, "confidence": float, "evidence": str}]
evidence must quote the specific measurements you used."""

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=config.NVIDIA_BASE_URL,
                         api_key=os.environ["NVIDIA_API_KEY"])
    return _client


def cached_chat(messages: list[dict], tag: str) -> str:
    """Every API response cached to disk keyed by input hash (demo survives no Wi-Fi)."""
    key = hashlib.sha256(
        json.dumps([tag, config.NEMOTRON_MODEL, messages], sort_keys=True).encode()
    ).hexdigest()
    path = config.CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())["content"]
    resp = client().chat.completions.create(
        model=config.NEMOTRON_MODEL, messages=messages,
        temperature=config.LLM_TEMPERATURE,
    )
    content = resp.choices[0].message.content or ""
    if content:  # never cache an empty response (would poison the demo cache)
        path.write_text(json.dumps({"content": content}))
    return content


def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def parse_events(raw: str) -> list[Event]:
    try:
        data = json.loads(strip_fences(raw))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    events: list[Event] = []
    for item in data:
        try:
            events.append(Event.model_validate(item))
        except ValidationError:
            continue
    return events


def judge(enriched: str) -> list[Event]:
    raw = cached_chat(
        [{"role": "system", "content": JUDGE_SYSTEM},
         {"role": "user", "content": enriched}],
        tag="judge",
    )
    return [e for e in parse_events(raw) if e.type != "false_alarm"]


Exercise = Literal["pacing_drill", "easy_onset", "pausing_practice", "repeat_passage"]


class PracticePlan(BaseModel):
    exercise: Exercise
    feedback: str


PLANNER_SYSTEM = """detailed thinking off
You are a supportive reading-practice coach (NOT a clinician; never diagnose).
Given measured metrics and classified moments from one read-aloud take, pick exactly
ONE exercise: pacing_drill, easy_onset, pausing_practice, or repeat_passage.
Write 2-3 encouraging sentences of feedback. Every number you mention MUST come
from the metrics given — do not invent counts or rates.
Reply with ONLY JSON: {"exercise": str, "feedback": str}"""


def grounded(feedback: str, metrics: dict) -> bool:
    """Reject feedback mentioning numbers not present in metrics."""
    allowed: set[str] = set()
    for v in metrics.values():
        if isinstance(v, (int, float)):
            allowed |= {str(v), str(int(v)), f"{float(v):.1f}", f"{float(v):.2f}"}
    numbers = re.findall(r"\d+(?:\.\d+)?", feedback)
    return all(n in allowed for n in numbers)


def plan(events: list[Event], metrics: dict) -> PracticePlan:
    payload = json.dumps({
        "metrics": metrics,
        "moments": [{"word": e.word, "type": e.type, "start": e.start} for e in events],
    })
    fallback = PracticePlan(exercise="repeat_passage",
                            feedback="Nice work getting a take down. Read the passage once more at an easy pace.")
    for attempt in ("plan", "plan_retry"):
        raw = cached_chat(
            [{"role": "system", "content": PLANNER_SYSTEM},
             {"role": "user", "content": payload}],
            tag=attempt,
        )
        try:
            candidate = PracticePlan.model_validate_json(strip_fences(raw))
        except ValidationError:
            continue
        if grounded(candidate.feedback, metrics):
            return candidate
    return fallback
