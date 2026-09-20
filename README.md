# 🎙️ SpeakR

**A read-aloud fluency practice companion.** You read a passage; SpeakR finds the moments where your speech and the text don't line up, uses **NVIDIA Nemotron** to decide what each moment actually was (a block, a prolongation, a repetition, a filler, or a false alarm), and hands back a grounded practice plan.

> SpeakR is a **practice companion, not a diagnostic or treatment tool.** It highlights moments in a recording to practice with — it does not assess or diagnose any condition.

Built for SteelHacks — **Best Use of NVIDIA Nemotron** track.

---

## What it does

- Pick a preset passage, **paste your own**, or **replay a cached recording** — then **record or upload** yourself reading.
- SpeakR shows:
  - a **metrics** line (WPM, % words matched, long pauses, speaking time),
  - the **transcript**, color-coded where a disfluency was flagged,
  - a **detected-moments table** — each with the type, a confidence, and the *measurement-based evidence* Nemotron used,
  - a **practice plan** — the sound you struggled with, a matching tongue twister, a breathing exercise, and one recommended drill.

## How it works

```
audio → transcribe → align to passage → detect speech regions → find mismatches
      → enriched transcript → Nemotron judge → Nemotron planner → UI
```

| Stage | Tool | What it produces |
|---|---|---|
| Transcribe | faster-whisper (disfluency-preserving settings) | words + timestamps |
| Align | difflib | matched / inserted / skipped / substituted |
| Speech regions | Silero VAD | where there's voice vs. silence |
| Mismatch flags | rules (`cadence/mismatch.py`) | stretched-word, mid-phrase-silence, unexplained-sound, repetition |
| Enriched transcript | `cadence/enrich.py` | per-word timing, `voiced_frac`, alignment status, flags |
| Judge | **Nemotron** | classifies each flagged moment into a disfluency type |
| Planner | **Nemotron** | one exercise + grounded feedback |

## How NVIDIA Nemotron is used

**The pipeline measures; Nemotron interprets and decides — it never computes the metrics.**

- **Judge** (`cadence/llm.py`): reads the enriched transcript and classifies each flagged moment. This is where the intelligence lives — e.g. a "stretched" word that's mostly silence (`voiced_frac` low) is called a **block**, not a prolongation; a naturally-long but fully-voiced word is rejected as a **false alarm**.
- **Planner**: picks one practice exercise and writes 2–3 encouraging sentences, passed through a **grounding check** that rejects any feedback citing numbers not in the measurements.
- Model: `nvidia/nemotron-3-super-120b-a12b` via NVIDIA's OpenAI-compatible API, with `detailed thinking off` for clean JSON. Every response is **cached to disk** so demos survive a dead network.

## Results

We evaluate three arms on labeled clips: **plain-transcript Nemotron** (no measurements), a **rules-only baseline**, and the **enriched Nemotron judge**. Match is by type + time overlap. (`python -m eval.run_eval` → `eval/results.md`.)

**Real recordings (own voice, 4 clips) — overall F1:**

| Arm | Precision | Recall | F1 |
|---|---|---|---|
| Plain-transcript Nemotron | 0.00 | 0.00 | **0.00** |
| Rules-only baseline | 0.15 | 0.40 | **0.22** |
| **Enriched Nemotron judge** | 0.39 | 0.70 | **0.50** |

Synthetic set (16 clips) tells the same story: **0.06 → 0.16 → 0.41**.

**The takeaway:** Nemotron *without* the measurements is useless (0.00), the measurements *without* Nemotron are weak (0.22), and the combination is the win (0.50) — it roughly **doubles the baseline** and catches 100% of word-repetitions and blocks on the real clips.

## Setup

```bash
brew install ffmpeg                     # required for audio decoding
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "NVIDIA_API_KEY=nvapi-..." > .env  # from build.nvidia.com
```

## Run

```bash
python app.py                 # the Gradio practice app
python -m eval.run_eval       # regenerate eval/results.md  (--quick for 4 clips)
python -m pytest -q           # tests
```

## Repo layout

```
cadence/
  config.py       thresholds, model name, paths
  transcribe.py   faster-whisper wrapper (keeps disfluencies)
  align.py        difflib passage alignment
  vad.py          Silero VAD
  mismatch.py     rule-based flags (incl. repetition detection)
  enrich.py       enriched transcript (+ voiced_frac)
  llm.py          Nemotron judge, planner, grounding check, disk cache
  baseline.py     rules-only classifier (eval comparison)
  coaching.py     problem-sound detection + practice recommendations
  pipeline.py     run_pipeline(audio, passage) -> result
app.py            Gradio UI
data/passages/    reading passages (incl. sound-loaded practice passages)
eval/run_eval.py  evaluation harness -> eval/results.md
```

## Known limitations (honest)

- **Prolongations are over-flagged.** The duration threshold is deliberately kept generic (not tuned to any speaker), so some fully-voiced long words trip it; the judge catches most but not all. Tuning it would overfit.
- **Some sound-repetitions are lost in transcription.** Whisper sometimes "cleans up" a stutter into fluent text; we mitigate this with disfluency-preserving settings, but what the transcriber discards can't be recovered downstream.
- **A brand-new recording takes up to ~90s** (two Nemotron calls). Cached clips are instant, and the UI shows a working state while it runs.

## Roadmap

- **ElevenLabs track:** spoken feedback, a target-pace model reading, and voice-clone playback.
- Progress tracking across sessions; free-speech (no-passage) mode.
