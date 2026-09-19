# Cadence — speech fluency practice companion

## Context
- Solo, 24-hour hackathon (SteelHacks). All code must be written during the event; open-source libraries and APIs are fine.
- Entering two tracks: **Best Use of NVIDIA Nemotron** and **Best Project Built with ElevenLabs**.
- Framing: a practice companion between sessions with a speech-language pathologist. NOT a diagnostic or treatment tool. Never write UI copy or feedback that diagnoses.
- Priority order: working end-to-end pipeline > evaluation with numbers > UI polish > extra features.

## What it does
User reads a known passage aloud (recorded or uploaded). Cadence finds where the audio and the transcript don't line up, Nemotron decides what each moment was (repetition, block, prolongation, filler, or false alarm), then picks one practice exercise with feedback grounded in measurements. The UI shows the transcript under the waveform with disfluencies highlighted.

## Pipeline
audio → transcribe → align to passage → detect speech regions → find mismatches → enriched transcript → Nemotron judge → Nemotron planner → Gradio display

1. **Transcribe**: faster-whisper with `word_timestamps=True` and a filler-keeping `initial_prompt` (e.g. "Umm, so, uh, I- I was like...").
2. **Align**: `difflib.SequenceMatcher` between transcript words and passage words → matched / skipped / inserted / substituted.
3. **Speech regions**: Silero VAD.
4. **Mismatches**:
   - Speech region with no overlapping word → `unexplained_sound` (likely dropped repetition or filler)
   - Word duration > ~2x expected for its syllable count → `stretched_word`
   - Gap > ~0.8s before a word, not after punctuation → `mid_phrase_silence`
   Keep thresholds in `config.py`.
5. **Enriched transcript**: text block per word with timing, gap before, duration vs expected, alignment status, and nearby flags.
6. **Nemotron judge**: returns JSON list, one item per flag:
   `{"word": str, "start": float, "type": "sound_repetition|word_repetition|prolongation|block|filler|false_alarm", "confidence": float, "evidence": str}`
   Also decides transcription error vs speaker misread for alignment mismatches.
7. **Nemotron planner**: picks ONE exercise (pacing_drill, easy_onset, pausing_practice, repeat_passage) + 2–3 sentences of feedback.
8. **Grounding check**: reject feedback that mentions numbers or events not present in the metrics; retry once.

## Rules for LLM use
- Nemotron never computes metrics; the pipeline measures, Nemotron interprets and decides.
- Always request JSON; strip code fences before parsing; validate with pydantic; handle failures without crashing.
- Nemotron via NVIDIA's OpenAI-compatible API (build.nvidia.com). Key in `.env` as `NVIDIA_API_KEY`. Model name in `config.py`.
- ElevenLabs key in `.env` as `ELEVENLABS_API_KEY`.
- Cache every API response to disk keyed by input hash (demo must work if Wi-Fi fails).

## ElevenLabs uses
- TTS: generate fluent readings of passages in several voices for synthetic test data.
- TTS: pacing model audio at a target rate chosen by Nemotron.
- Scribe STT (`scribe_v2`): comparison transcriber in the eval only.

## Repo layout
```
cadence/
  config.py            thresholds, model names, paths
  transcribe.py        faster-whisper + scribe wrappers
  align.py             passage alignment
  vad.py               Silero VAD
  mismatch.py          mismatch detection
  enrich.py            enriched transcript builder
  llm.py               Nemotron client, judge, planner, grounding check
  tts.py               ElevenLabs TTS helpers
  pipeline.py          run_pipeline(audio_path, passage) -> result dict
  baseline.py          rules-only classifier for comparison
app.py                 Gradio UI
data/
  passages/            public-domain reading passages (.txt)
  demo/                4–5 pre-recorded demo clips
  synthetic/           generated clips + labels.json
  real/                own recordings + labels.json
scripts/
  make_synthetic.py    ElevenLabs fluent audio + pydub disfluency insertion with exact labels
eval/
  run_eval.py          all experiments -> eval/results.md + charts
cache/
```

## Label format (labels.json)
`[{"clip": "file.wav", "passage": "id", "events": [{"type": "sound_repetition", "word_index": 3, "start": 1.20, "end": 1.65}]}]`
Fluent clips have `"events": []`.

## Synthetic data (scripts/make_synthetic.py)
Take a fluent TTS reading + its word timestamps, then insert at recorded positions:
- sound repetition: copy first ~80ms of a word 2–3 times with short gaps
- block: insert 1.0–2.0s silence before a word
- prolongation: time-stretch the first ~150ms of a word to 3–4x
Write exact labels. Keep ~20% of clips untouched.

## Evaluation (eval/run_eval.py)
1. Detection recall/precision per disfluency type
2. Nemotron judge vs rules-only baseline (accuracy, per-type F1)
3. False alarm rate on fluent clips
4. Nemotron with plain transcript vs enriched transcript
5. Whisper vs Scribe: % of labeled disfluencies preserved in the transcript
6. Grounding check pass rate for feedback
7. Synthetic vs real accuracy
8. Save 3–4 failure cases with explanations
Match predicted events to labels by type + time overlap (tolerance ~0.3s).

## Gradio app (app.py)
- Passage picker + "hear target pace" button
- Buttons for each demo clip + upload/record
- Waveform audio player, `HighlightedText` transcript color-coded by event type
- Event list (word, type, confidence, evidence), recommended exercise, feedback
- Small "clips are pre-recorded" note; disclaimer that this is a practice tool, not diagnosis

## Build order (finish each before starting the next)
1. Env + API smoke tests for Nemotron and ElevenLabs + Gradio hello world
2. transcribe.py + align.py working on one clip
3. vad.py + mismatch.py
4. make_synthetic.py + record real clips
5. enrich.py + llm.py judge + baseline.py
6. run_eval.py with first numbers
7. app.py
8. Planner, grounding check, pacing audio
9. Scribe comparison
10. Final eval, cache demo results, README, backup video

## Cut list (in order, if behind)
noise experiment → Scribe comparison → pacing audio → planner. Never cut the eval.

## Code style
Python 3.11, type hints, small pure functions, no notebooks. Print progress in scripts. Prefer simple and working over clever.