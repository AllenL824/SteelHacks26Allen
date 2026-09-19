import hashlib
import json
import os
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
