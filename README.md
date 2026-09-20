1# 🎙️ SpeakR

> **SpeakR is a read-aloud speech-practice companion that measures where you stumble while reading a passage, uses NVIDIA Nemotron to classify each moment (block, prolongation, repetition, or filler) and generate grounded coaching, then speaks that feedback — and even reads the passage back fluently in your own ElevenLabs-cloned voice.**

You read a passage aloud; SpeakR finds the moments where your speech and the text don't line up, uses **NVIDIA Nemotron** to decide what each moment actually was — a block, a prolongation, a repetition, a filler, or a false alarm — and hands back a grounded practice plan you can **hear coached in a real voice** and even **played back fluently in your own cloned voice**.

> SpeakR is a **practice companion, not a diagnostic or treatment tool.** It highlights moments in a recording to practice with — it does not assess or diagnose any condition.

Built for SteelHacks — **Best Use of NVIDIA Nemotron** and **Best Use of ElevenLabs**.

---

## What it does

1. **Choose a passage** — a preset, or **write your own**.
2. **Record, upload an audio file, or replay a cached sample.**
3. **Analyze** → SpeakR shows:
   - a **metrics** line (WPM, % words matched, long pauses, speaking time);
   - a **waveform** with each detected moment shaded by type — a block shows as a flat silent gap, a prolongation as a sustained stretch;
   - the **transcript**, color-coded where a disfluency was flagged;
   - a **detected-moments table** — each with its type, a confidence, and the *measurement-based evidence* Nemotron used;
   - a **practice plan** — the sound you struggled with, a matching tongue twister, a breathing exercise, and one recommended drill.
4. **Listen (ElevenLabs):**
   - **🔊 Coach me** — a spoken coaching debrief (Nemotron writes it, ElevenLabs speaks it);
   - **🎙️ Hear it in your own voice** — your voice, cloned from your recording, reading the passage fluently.

## How it works

```
audio → transcribe → align to passage → detect speech regions → find mismatches
      → enriched transcript → Nemotron judge → Nemotron planner → UI + ElevenLabs voice
```

| Stage | Tool | What it produces |
|---|---|---|
| Transcribe | faster-whisper (disfluency-preserving settings) | words + timestamps |
| Align | difflib | matched / inserted / skipped / substituted |
| Speech regions | Silero VAD | where there's voice vs. silence |
| Mismatch flags | rules (`speakr/mismatch.py`) | stretched-word, mid-phrase-silence, unexplained-sound, repetition |
| Enriched transcript | `speakr/enrich.py` | per-word timing, `voiced_frac`, alignment status, flags |
| **Judge** | **Nemotron** | classifies each flagged moment into a disfluency type |
| **Planner** | **Nemotron** | one exercise + grounded feedback |
| Voice | ElevenLabs | spoken coach debrief + user's-own-voice playback |

## How NVIDIA Nemotron is used

**The pipeline measures; Nemotron interprets and decides — it never computes the metrics.**

- **Judge** (`speakr/llm.py`): reads the enriched transcript and classifies each flagged moment. This is where the intelligence lives — e.g. a "stretched" word that's mostly silence (`voiced_frac` low) is called a **block**, not a prolongation; a naturally-long but fully-voiced word is rejected as a **false alarm**; a repeated word/fragment becomes a **repetition**.
- **Planner**: picks one practice exercise and writes 2–3 encouraging sentences, passed through a **grounding check** that rejects any feedback citing numbers not present in the measurements (retries once, then falls back).
- Model: `nvidia/nemotron-3-super-120b-a12b` via NVIDIA's OpenAI-compatible API, with `detailed thinking off` for clean JSON. Every response is **cached to disk** so demos survive a dead network.

## How ElevenLabs is used

Integral to the coaching loop, not bolted on:
- **Coach me** — the practice debrief Nemotron writes (feedback + your problem sound + a tongue-twister drill) is spoken aloud in a natural voice, so the feedback becomes an *audio drill you can imitate*.
- **Hear it in your own voice** — instant voice-cloning from the user's recording, then the passage read back *fluently in their own voice* ("here's you, smooth"). Reuses a single voice slot; all audio cached to disk.

## Results

Three arms on labeled clips: **plain-transcript Nemotron** (transcript only, no measurements), a **rules-only baseline**, and the **enriched Nemotron judge**. Match is by type + time overlap. (`python -m eval.run_eval` → `eval/results.md`.)

**Real recordings (own voice, 4 clips) — overall F1:**

| Arm | Precision | Recall | F1 |
|---|---|---|---|
| Plain-transcript Nemotron | 0.00 | 0.00 | **0.00** |
| Rules-only baseline | 0.15 | 0.40 | **0.22** |
| **Enriched Nemotron judge** | 0.39 | 0.70 | **0.50** |

Synthetic set (16 clips) tells the same story: **0.06 → 0.16 → 0.41**.

**The takeaway:** Nemotron *without* the measurements is useless (0.00); the measurements *without* Nemotron are weak (0.22); the combination roughly **doubles the baseline** (0.50) and catches 100% of word-repetitions and blocks on the real clips. That three-way gap is the core evidence that the measure-then-interpret design is what works.

## Privacy by design

No accounts, no cloud database. Audio is processed and cached **on your machine**; nothing is uploaded to a server we own (Nemotron/ElevenLabs are called only to interpret measurements and generate voice). Deleting the local cache removes everything. For a speech tool, running locally is a deliberate privacy choice, not a missing feature.

## Setup

```bash
brew install ffmpeg                          # required for audio decoding
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                          # then fill in your keys:
#   NVIDIA_API_KEY=nvapi-...   (from build.nvidia.com — required)
#   ELEVENLABS_API_KEY=...     (from elevenlabs.io — optional; enables the voice buttons)
```

## Run

```bash
python app.py                 # the Gradio practice app
python -m eval.run_eval       # regenerate eval/results.md  (--quick for 4 clips)
python -m pytest -q           # 43 tests
```

## Repo layout

```
speakr/
  config.py         thresholds, model name, paths
  transcribe.py     faster-whisper wrapper (keeps disfluencies)
  align.py          difflib passage alignment
  vad.py            Silero VAD (ffmpeg-backed decode: any audio format)
  mismatch.py       rule-based flags (incl. repetition detection)
  enrich.py         enriched transcript (+ voiced_frac)
  llm.py            Nemotron judge, planner, grounding check, disk cache
  baseline.py       rules-only classifier (eval comparison)
  coaching.py       problem-sound detection + practice recommendations
  voice.py          ElevenLabs coach debrief + voice clone (app-only)
  pipeline.py       run_pipeline(audio, passage) -> result
app.py              Gradio UI
data/passages/      reading passages (incl. sound-loaded practice passages)
eval/run_eval.py    evaluation harness -> eval/results.md
```

## Architecture notes & future work

We deliberately split **measurement** (signal processing) from **interpretation** (Nemotron). We validated this: feeding the judge *more numeric acoustic features* (spectral stationarity) produced **no eval gain** — because a bottleneck trace showed the misses are **upstream of the judge**, not in classification:

- **one flag → one event per word**, so a word that is *both* a block and a sound-repetition can only score one;
- a **generic duration threshold** gates which moments reach the judge at all;
- **ASR normalization** occasionally erases a stutter before anything downstream sees it.

The judge classifies what it's given well; recall is limited by the detection layer. The principled **v2** would replace the rule-flag + LLM-judge classifier with a **frame-level acoustic disfluency model** (e.g. wav2vec2 fine-tuned on SEP-28k), which works on raw audio (immune to ASR normalization), needs no hand threshold, and can emit stacked/overlapping events — removing all three bottlenecks.

## Known limitations (honest)

- **Prolongations are over-flagged.** The duration threshold is kept generic (not tuned to any speaker), so some fully-voiced long words trip it. Tuning it would overfit our small eval.
- **Some sound-repetitions are lost in transcription** — Whisper sometimes cleans a stutter into fluent text; disfluency-preserving settings help, but what the transcriber discards can't be recovered downstream.
- **A brand-new recording takes up to ~90s** (two Nemotron calls). Cached clips are instant, and the UI shows a working state while it runs.
