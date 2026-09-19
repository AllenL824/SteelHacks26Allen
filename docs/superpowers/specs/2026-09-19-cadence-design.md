# Cadence — design spec

**Date:** 2026-09-19
**Event:** SteelHacks 2026, solo, 24 hours
**Tracks:** Best Use of NVIDIA Nemotron (primary), Best Project Built with ElevenLabs (secondary, additive)

## 1. Summary

Cadence is a practice companion for people who stutter. The user reads a known
passage aloud; Cadence finds the moments where the speech and the passage stop
lining up, has Nemotron classify each moment (repetition, block, prolongation,
filler, or false alarm), and recommends one exercise with feedback grounded in
measurements. Optionally, ElevenLabs speaks the feedback and plays the passage
back fluently in the user's own voice.

It is a practice tool between sessions with a speech-language pathologist. It
is **not** diagnostic. No UI copy or generated feedback may diagnose, name a
disorder, or assess severity.

### Rules that shape everything

- **The code measures, the LLM interprets.** Nemotron never computes a number.
  It receives measurements and decides what they mean.
- **Labels are ground truth, not model output.** Evaluation data is constructed
  (disfluencies spliced into clean audio at recorded positions), so the answer
  key is exact and independent of any model.
- **Nothing on the critical path touches the network except Nemotron.** Synthetic
  data uses local macOS `say`. ElevenLabs is layered on last and imported only
  by the UI.
- **Every external API response is cached to disk** keyed by input hash. The
  demo must run with Wi-Fi off.
- **Hackathon rule:** all code is written during the event. The prior `Speech`
  repo is a design reference only; nothing is copied from it.

## 2. User flow

1. Pick a passage (3–4 public-domain passages, including the Rainbow Passage
   and Grandfather Passage, which are standard SLP reading texts).
2. Record in the browser, upload a file, or pick a pre-recorded demo clip.
3. Wait a few seconds.
4. See: waveform player; the transcript with disfluent words color-coded by
   type; an event list (word, type, confidence, one-line evidence); one
   recommended exercise; 2–3 sentences of feedback.
5. Hear the feedback spoken (ElevenLabs TTS).
6. Optionally press "Hear it fluent" to play the passage read smoothly in a
   clone of the user's own voice at the pace Nemotron chose (ElevenLabs IVC).
7. A visible note says demo clips are pre-recorded and that Cadence is a
   practice tool, not a diagnosis.

## 3. Pipeline

```
audio file
  → audio.load_audio          16 kHz mono float32 via ffmpeg
  → transcribe.transcribe     faster-whisper, word timestamps, filler-keeping prompt
  → align.align               difflib against passage tokens
  → vad.speech_regions        Silero VAD (onnxruntime, no torch)
  → mismatch.find_flags       unexplained_sound / stretched_word / mid_phrase_silence
  → enrich.build_transcript   one text block per word with timing + flags
  → llm.judge                 Nemotron → list[Event]
  → metrics.summarize         counts, rate, longest gap (pure functions)
  → llm.plan                  Nemotron → one exercise + feedback
  → llm.grounding_check       reject feedback citing numbers/events not in metrics
  → Result                    dict consumed by app.py and eval
```

`baseline.rules_judge` is a deterministic alternative to `llm.judge` used only
by the eval.

## 4. Modules

All under `cadence/`. Python 3.11, type hints, small pure functions, no
notebooks. Each module exposes the functions listed and nothing else is relied
on by other modules.

### `config.py`
Constants only. Thresholds: `GAP_SEC = 0.8`, `STRETCH_RATIO = 2.0`,
`SEC_PER_SYLLABLE = 0.2`, `MIN_UNEXPLAINED_SEC = 0.15`, `EVAL_TOLERANCE_SEC = 0.3`.
Model ids: `NEMOTRON_MODEL` (default candidate
`nvidia/llama-3.3-nemotron-super-49b-v1.5`; confirm the exact id on
build.nvidia.com during step 0), `WHISPER_MODEL = "base.en"`,
`WHISPER_COMPUTE = "int8"`. Paths: `DATA_DIR`, `CACHE_DIR`. ElevenLabs voice id
for spoken feedback.

### `types.py`
Dataclasses:
- `Word(text, start, end)` — ASR output.
- `PassageWord(text, index, ends_sentence: bool)`.
- `AlignedWord(status: "match"|"substitute"|"omit"|"insert", passage_index: int|None, asr_index: int|None)`.
- `SpeechRegion(start, end)`.
- `Flag(kind: "unexplained_sound"|"stretched_word"|"mid_phrase_silence", start, end, word_index: int|None, detail: str)`.
- `Event(word: str, start: float, end: float, type: EventType, confidence: float, evidence: str)` where
  `EventType = "sound_repetition"|"word_repetition"|"prolongation"|"block"|"filler"|"false_alarm"`.
- `Plan(exercise: "pacing_drill"|"easy_onset"|"pausing_practice"|"repeat_passage", feedback: str, target_wpm: int)`.
- `Result` — everything above plus `metrics: dict` and `passage_id`.

### `audio.py`
`load_audio(path) -> np.ndarray` (16 kHz mono float32) via `ffmpeg` subprocess.
`save_wav(path, samples)`. Handles m4a/mp3/webm/wav.

### `passages.py`
`load_passage(passage_id) -> list[PassageWord]` from `data/passages/<id>.txt`.
`list_passages() -> list[str]`. Tokenizer lowercases, strips punctuation, marks
`ends_sentence` on the token before `.?!;`. `syllables(word) -> int` — vowel-group
heuristic, used for expected duration.

### `transcribe.py`
`transcribe(samples) -> list[Word]`. faster-whisper `base.en` int8 on CPU,
`word_timestamps=True`, `initial_prompt="Umm, so, uh, I- I was like, um, you know..."`
to discourage filler removal. Also `transcribe_scribe(path) -> list[Word]`
(ElevenLabs Scribe v2) used only by the eval; wrapped so an import failure or
missing key returns `None`.

### `align.py`
`align(passage: list[PassageWord], asr: list[Word]) -> list[AlignedWord]` using
`difflib.SequenceMatcher` on normalized tokens. `equal` → match; `replace` →
substitute (pairwise) with extra ASR words as insert and extra passage words as
omit; `delete` → omit; `insert` → insert.

### `vad.py`
`speech_regions(samples) -> list[SpeechRegion]` via silero-vad ONNX model with
onnxruntime. Merge regions separated by < 0.1 s.

### `mismatch.py`
`find_flags(passage, aligned, asr, regions) -> list[Flag]`:
- **unexplained_sound**: a speech region (or sub-span) of ≥ `MIN_UNEXPLAINED_SEC`
  with no overlapping ASR word.
- **stretched_word**: an ASR word whose duration > `STRETCH_RATIO × syllables × SEC_PER_SYLLABLE`.
- **mid_phrase_silence**: gap > `GAP_SEC` between consecutive ASR words where the
  preceding word's aligned passage word does not have `ends_sentence`.
Pure function; no I/O.

### `enrich.py`
`build_transcript(passage, aligned, asr, flags) -> str`. One line per ASR word:
`[12] "disputing" 3.21–3.58 (0.37s, expected 0.60s) gap_before=1.42s status=match flags=[mid_phrase_silence]`
plus a header with passage id, total duration, and a list of unexplained-sound
spans. Also `build_plain_transcript(asr) -> str` (just words) for eval #4.

### `llm.py`
Nemotron via the OpenAI-compatible endpoint (`https://integrate.api.nvidia.com/v1`),
key from `NVIDIA_API_KEY` in `.env`. All calls go through `cache.cached_call`.
- `judge(enriched: str) -> list[Event]`. Prompt asks for a JSON array only, one
  item per flagged moment, with `false_alarm` allowed. Also asks it to decide,
  for each substitute/insert/omit, whether it is a transcription error or a
  speaker misread; misreads that look like repetitions become events.
- `plan(events, metrics) -> Plan`. Exactly one exercise; 2–3 sentences; must
  mention only numbers present in `metrics`.
- `grounding_check(plan, metrics, events) -> bool`. Extract every number in
  `plan.feedback`; each must equal (±rounding) a value in `metrics`. Every
  event type named must appear in `events`. On failure `plan` is retried once
  with the violation appended to the prompt; on second failure a templated
  fallback feedback is used.
- Parsing: strip code fences, `json.loads`, validate with pydantic models.
  Any failure → log, return `[]` / fallback plan. Never raise to the UI.

### `baseline.py`
`rules_judge(flags, aligned, asr) -> list[Event]`, deterministic:
`mid_phrase_silence → block`, `stretched_word → prolongation`,
`unexplained_sound → sound_repetition`, an `insert` whose text equals the
previous word → `word_repetition`, an `insert` in {um, uh, er, like} → `filler`.
Confidence fixed at 0.5.

### `metrics.py`
`summarize(asr, aligned, events, duration) -> dict`: `wpm`, `event_counts` by
type, `longest_gap_sec`, `total_events`, `passage_words`, `words_spoken`,
`accuracy` (matches ÷ passage words). Pure functions.

### `cache.py`
`cached_call(namespace, key_obj, fn)`. SHA-256 of `json.dumps(key_obj, sort_keys=True)`
→ `cache/<namespace>/<hash>.json` (or `.wav` for audio). Used by `llm.py`,
`voice.py`, and `transcribe.transcribe_scribe`.

### `voice.py` (ElevenLabs, additive)
Imported only by `app.py`. Key from `ELEVENLABS_API_KEY`.
- `speak(text) -> wav path` — feedback TTS in a fixed warm voice.
- `clone_voice(audio_path) -> voice_id` — Instant Voice Cloning from the user's
  recording (or a pre-made clone for demo clips).
- `read_passage(passage_text, voice_id, target_wpm) -> wav path`.
Every function catches all exceptions and returns `None`; the UI hides the
audio component when it gets `None`.

### `pipeline.py`
`run_pipeline(audio_path, passage_id, judge="nemotron"|"rules", transcript="enriched"|"plain") -> Result`.
The two keyword arguments exist so the eval can run the four ablations without
duplicating code.

## 5. Data

```
data/
  passages/       rainbow.txt, grandfather.txt, north_wind.txt (+1 optional)
  demo/           4–5 pre-recorded clips of the author reading, with results cached
  synthetic/      generated clips + labels.json
  real/           author's own recordings + hand-written labels.json
```

### Label format (`labels.json`)
```json
[{"clip": "clip_012.wav", "passage": "rainbow", "voice": "Samantha",
  "events": [{"type": "block", "word_index": 7, "start": 3.21, "end": 4.61}]}]
```
Fluent clips have `"events": []`.

### Synthetic generation (`scripts/make_synthetic.py`)
For each (passage × voice × rate) combination:
1. `say -v <voice> -r <wpm> -o fluent.aiff --data-format=LEI16@22050 "<passage>"`,
   then `ffmpeg` → 16 kHz wav. Voices rotated from the installed `say` list
   (checked at runtime; e.g. Samantha, Alex, Fred, Eddy, Flo). Rates 150–200 wpm.
2. Transcribe the fluent clip with `transcribe.transcribe` to get word times.
   (Whisper on clean TTS is accurate; the eval writeup states this caveat.)
3. Choose 1–4 target words at random and insert, working back-to-front so
   earlier timestamps stay valid:
   - **sound_repetition**: copy the first 80 ms of the word, repeat 2–3× with
     60–100 ms silences, placed immediately before the word.
   - **block**: insert 1.0–2.0 s of near-silence (−60 dBFS noise) before the word.
   - **prolongation**: tile the first 150 ms of the word 3–4× with 10 ms
     crossfades (a simple stretch; pitch-preserving stretch is out of scope).
   - **filler** (if time): splice a pre-rendered `say` "um" before the word.
4. Write the label with exact `start`/`end` from the insertion arithmetic.
5. Leave ~20% of clips untouched (`events: []`).
Target: ~40–60 clips, ~120+ events. Runs offline in under two minutes.

## 6. Evaluation (`eval/run_eval.py`)

Matching rule: a predicted event matches a label if types are equal and the
time spans overlap within `EVAL_TOLERANCE_SEC`. Each label matches at most one
prediction. `false_alarm` predictions are treated as "no event".

Experiments, each printed and written to `eval/results.md` with matplotlib
charts in `eval/charts/`:
1. Detection recall/precision per type (flags stage only, before any judge).
2. Nemotron judge vs rules baseline: accuracy, per-type F1.
3. False-alarm rate on fluent clips (both judges).
4. Nemotron with enriched transcript vs plain transcript.
5. Whisper vs Scribe: % of labeled disfluencies still visible in the transcript
   (skipped with a note if Scribe is unavailable).
6. Grounding-check pass rate on first attempt.
7. Synthetic vs real accuracy.
8. 3–4 failure cases saved with the enriched transcript and an explanation.

The eval is never cut.

## 7. UI (`app.py`, Gradio)

- Passage dropdown; "Hear target pace" button (ElevenLabs; hidden if unavailable).
- Demo-clip buttons; `gr.Audio` for record/upload.
- `gr.Audio` waveform player of the analysed clip.
- `gr.HighlightedText` transcript, color per event type, legend shown.
- Event table: word, type, confidence, evidence.
- Recommended exercise + feedback text; `gr.Audio` of spoken feedback.
- "Hear it fluent" button → cloned-voice fluent reading.
- Footer: "Demo clips are pre-recorded. Cadence is a practice tool, not a
  diagnosis. Talk to a speech-language pathologist about your speech."

## 8. Error handling

- Nemotron unreachable or unparsable → fall back to `rules_judge` and templated
  feedback, with a small "offline mode" badge. Never crash.
- ElevenLabs unreachable → hide audio components; text remains.
- Empty transcript (silence) → friendly message, no analysis.
- Unsupported audio → `audio.load_audio` raises a clear error the UI displays.

## 9. Testing

`pytest` under `tests/`. Fast, no network, no model downloads:
- `test_align.py`: exact, omission, insertion, substitution, repeated word.
- `test_mismatch.py`: each flag kind fires on constructed inputs; sentence-final
  gaps do not fire.
- `test_baseline.py`: mapping table.
- `test_grounding.py`: accepts grounded feedback; rejects an invented number.
- `test_eval_matching.py`: tolerance and one-to-one matching.
- `test_synthetic.py`: inserting a block shifts later word times by exactly the
  inserted duration; label positions are consistent with the written wav.
- `test_llm_parsing.py`: code-fence stripping, malformed JSON → `[]`.
Model-dependent stages (`transcribe`, `vad`) are covered by one component test
that runs only when `RUN_SLOW=1`.

## 10. Build order

| # | Step | Est. |
|---|---|---|
| 0 | `brew install ffmpeg`; venv; `.env`; Nemotron smoke test; Gradio hello world | 1h |
| 1 | `types.py`, `audio.py`, `passages.py`, `transcribe.py`, `align.py` on one clip | 1.5h |
| 2 | `vad.py`, `mismatch.py` | 2h |
| 3 | `scripts/make_synthetic.py` → `data/synthetic/` + `labels.json` | 2h |
| 4 | `enrich.py`, `cache.py`, `llm.judge`, `baseline.py`, `metrics.py` | 3h |
| 5 | `eval/run_eval.py` → first numbers (experiments 1–4) | 2h |
| 6 | `app.py` | 3h |
| 7 | `llm.plan`, `grounding_check`, experiment 6 | 1h |
| 8 | Record + hand-label real clips; demo clips; experiment 7 | 1h |
| 9 | `voice.py`: spoken feedback, then voice clone + fluent reading | 2h |
| 10 | Scribe (exp. 5), final eval, cache demo results, README, backup video | 1.5h |

Steps 0–5 are non-negotiable. After step 5 the project is submittable.

**Cut list, in order:** Scribe comparison → planner (use templated feedback) →
voice clone. Spoken feedback stays (ten minutes). The eval is never cut.

## 11. Risks

- **ffmpeg missing** on the dev machine — install first.
- **Nemotron model id** may differ from the default — verify in step 0.
- **ElevenLabs IVC gated** on the account tier — check in step 9; fall back to a
  stock voice framed as "a fluent model reading at your target pace".
- **Whisper drops repetitions** (its language model smooths them away). This is
  expected and is exactly why `unexplained_sound` exists; experiment 5 measures
  it.
- **Time.** 20h of work against ~18–19h available. The cut list exists for this.

## 12. Out of scope

Authentication, persistence, user history, multi-user, deployment, real-time
streaming analysis, pitch-preserving time stretch, any clinical scoring scale.
