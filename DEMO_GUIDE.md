# SpeakR — Demo & Pitch Guide

Everything you need to present SpeakR: the story, the slide deck, the live-demo
script, and the safety net. Read this once, rehearse the demo twice.

---

## The one-sentence pitch

> **SpeakR turns a read-aloud recording into a personalized speech-practice
> session — measuring where you stumble, using NVIDIA Nemotron to understand
> *what kind* of stumble it was, and coaching you back in your own voice with
> ElevenLabs.**

## The core idea (say this early, it's your differentiator)

> **The pipeline measures; Nemotron interprets.** Signal processing finds the
> suspicious moments and the numbers behind them; Nemotron decides what each one
> actually was and how to coach it. We proved this split matters — see the numbers.

---

## The killer slide: the three-arm result

This is your strongest 15 seconds. Put it on one slide as a bar chart:

| | F1 |
|---|---|
| Nemotron on the transcript alone | **0.00** |
| Rules/measurements alone | **0.22** |
| **Measurements + Nemotron (SpeakR)** | **0.50** |

Say: *"The LLM with no measurements is useless. The measurements with no LLM are
weak. Together they double the baseline. That gap is the whole thesis."*

---

## Slide deck (7 slides, ~4 minutes)

1. **Title + hook** — "SpeakR: practice reading aloud; get coached like a pro."
   One line: practice companion, *not* a diagnostic tool.
2. **The problem** — reading aloud / fluency practice is lonely; generic
   speech-to-text tells you *what* you said, not *how* — where you blocked,
   prolonged, repeated. (First-person reason if you have one — it lands.)
3. **How it works** — the pipeline diagram (audio → transcribe → align → VAD →
   flags → **Nemotron judge** → **Nemotron planner** → voice). Emphasize
   "measure, then interpret."
4. **Nemotron doing the thinking** — one real example: a 2-second "word" that's
   80% silence → the rules just see "long," Nemotron reads `voiced_frac` and
   correctly calls it a **block**, not a prolongation. Show the evidence string.
5. **The result** — the three-arm bar chart. This is the money slide.
6. **Live demo** — switch to the app (script below).
7. **Depth + future work** — one line each: honest limitations, the bottleneck
   is upstream of the LLM, and the v2 (wav2vec2 frame-level detector on SEP-28k).
   This shows you understand the problem, not just that you built something.

---

## Live demo script (~2.5 minutes)

**Before you start:** `python app.py`, open the URL, and make sure the cached
sample clips work offline (they do — responses are cached to disk). Have the
window already open on the right passage.

1. **Clean read (10s).** Replay **"🙂 Clean — North Wind."** Analyze → *"Clean
   read, no false alarms — it doesn't cry wolf."* (This one comes back clean.)
2. **Stutter read (40s).** Replay **"🗣️ Stutter — Rainbow."** Analyze. Walk the
   output top to bottom:
   - the metrics line;
   - **the waveform** — *"you can see the blocks as flat silent gaps and the
     prolongations as sustained stretches"* (point at a blue span on a silence);
   - the color-coded transcript;
   - the evidence table — read one evidence string aloud
     (*"voiced_frac=0.18 → block, not prolongation"*).
3. **The practice plan (15s).** *"It found the sound I struggle with and picked a
   matching drill."*
4. **ElevenLabs — Coach me (20s).** Click **🔊 Coach me.** Let a few seconds
   play. *"Nemotron wrote that coaching; ElevenLabs is speaking it."*
5. **ElevenLabs — your own voice (25s).** Click **🎙️ Hear it in your own voice.**
   *"It cloned my voice from the recording and read the passage back fluently —
   here's me, but smooth."* **This is your emotional peak — end the demo here.**
6. **(Optional) Custom passage / live record.** If Wi-Fi and mic are reliable,
   type a custom passage or record live to prove it's not hardcoded. Skip if
   risky — the cached clips already prove the point.

**Timing note:** a brand-new recording takes up to ~90s (two Nemotron calls).
For the demo, **lead with the cached samples** (instant). Only do a live
recording if you have time to fill while it runs.

---

## Handling likely judge questions

- **"Is this a medical/diagnostic tool?"** → No, and we're explicit about it —
  it's a practice companion. Never diagnoses.
- **"How accurate is it?"** → Honest: real-clip F1 ~0.50, roughly double the
  rules baseline, on a deliberately small hand-labeled set. We know the misses
  are upstream of the LLM (detection layer), not the classification.
- **"Where's the data stored / privacy?"** → Nothing persisted to a cloud we
  own. Audio is processed and cached locally; delete the cache and it's gone.
- **"Why Nemotron and not just rules?"** → The three-arm result: rules alone get
  0.22, Nemotron adds the judgment that takes it to 0.50 (e.g. silence-vs-held
  sound, false-alarm rejection). Show the slide.
- **"Could you scale accuracy?"** → Yes — v2 swaps the rule+LLM classifier for a
  wav2vec2 frame-level model fine-tuned on SEP-28k; works on raw audio, no
  threshold, emits stacked events. (Names the exact path — sounds like you know
  the field.)

---

## Safety net (do these before you present)

- [ ] **Record a 90-second backup video** of the full demo (clean → stutter →
      coach → clone). If the live demo fails, you play this. Non-negotiable.
- [ ] **Warm the cache**: run every sample clip through Analyze + Coach me +
      voice clone once, so they're instant and Wi-Fi-proof on stage.
- [ ] **Keys in `.env`** (NVIDIA required; ElevenLabs for the voice buttons).
- [ ] Test audio **output** on the presentation machine — the ElevenLabs moments
      need sound. A muted demo kills the second track.
- [ ] Have the **GitHub repo** and the **README's three-arm table** ready to show.

---

## What to lead with, if you only get 60 seconds

The hook + the three-arm result slide + the **voice-clone** moment. That's the
innovation, the proof, and the wow — one each.
