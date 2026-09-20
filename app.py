import gradio as gr

from cadence import config
from cadence.pipeline import load_passage, run_pipeline

try:  # ElevenLabs is optional — a missing key just hides the voice UI
    from cadence import voice
    VOICE_OK = voice.available()
except Exception:
    voice = None
    VOICE_OK = False

EVENT_COLORS = {
    "sound_repetition": "#e07b39",
    "word_repetition": "#d94f4f",
    "prolongation": "#7b5ce0",
    "block": "#3980e0",
    "filler": "#39b0a8",
}

DISCLAIMER = (
    "SpeakR is a practice companion, not a diagnostic or treatment tool. "
    "It highlights moments in a recording to practice with — it does not assess "
    "or diagnose any condition."
)

CUSTOM_OPTION = "✏️ Create your own…"


def passage_ids() -> list[str]:
    return sorted(p.stem for p in config.PASSAGES_DIR.glob("*.txt"))


def demo_catalog() -> list[tuple[str, str, str]]:
    """Curated cached recordings: (label, wav path, passage id).

    Only clips that exist on disk are offered, so the list degrades gracefully.
    """
    candidates = [
        ("🙂 Clean — Rainbow", config.DATA_DIR / "real" / "rainbow_clean.wav", "rainbow"),
        ("🗣️ Stutter — Rainbow", config.DATA_DIR / "real" / "rainbow_stutter.wav", "rainbow"),
        ("🙂 Clean — North Wind", config.DATA_DIR / "real" / "northwind_clean.wav", "north_wind"),
        ("🗣️ Stutter — North Wind", config.DATA_DIR / "real" / "northwind_stutter.wav", "north_wind"),
    ]
    return [(label, str(path), pid) for label, path, pid in candidates if path.exists()]


def highlighted(result) -> list[tuple[str, str | None]]:
    """(word, label) pairs for gr.HighlightedText, label = event type or None."""
    event_starts = [(e.start, e.type) for e in result["events"]]
    out = []
    for w in result["words"]:
        label = None
        for start, etype in event_starts:
            if abs(w.start - start) <= config.MATCH_TOLERANCE:
                label = etype
                break
        out.append((w.text + " ", label))
    return out


def render_waveform(audio_path: str, result):
    """Waveform of the audio with each detected moment shaded by type — you can
    literally see a block as a flat/silent gap and a prolongation as a sustained
    stretch. Returns a matplotlib Figure (or None on any failure)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        from cadence.vad import _read_audio
        wav = _read_audio(audio_path).numpy()
        sr = 16000
        t = np.arange(len(wav)) / sr
        step = max(1, len(wav) // 4000)  # downsample for a light plot

        fig, ax = plt.subplots(figsize=(11, 2.4))
        ax.plot(t[::step], wav[::step], color="#b8c0cc", linewidth=0.6)
        ax.set_yticks([])
        ax.set_ylim(-1.05, 1.05)
        ax.set_xlabel("time (seconds)", fontsize=8)
        ax.margins(x=0)

        words = result.get("words", [])
        seen: set[str] = set()
        for e in result["events"]:
            w = min(words, key=lambda w: abs(w.start - e.start)) if words else None
            start = e.start
            end = w.end if (w and abs(w.start - e.start) <= 0.35) else e.start + 0.3
            ax.axvspan(start, end, color=EVENT_COLORS.get(e.type, "#888"), alpha=0.35,
                       label=e.type.replace("_", " ") if e.type not in seen else None)
            seen.add(e.type)
        if result["events"]:
            ax.legend(loc="upper right", fontsize=7, framealpha=0.9, ncol=2)
        ax.set_title("Waveform — detected moments shaded", fontsize=9, loc="left")
        fig.tight_layout()
        return fig
    except Exception:
        return None


def _run_analysis(audio_path: str, passage: str):
    """Run the pipeline and format the outputs (metrics, waveform, transcript, events,
    plan, spoken-coach script). Blocking (no progress)."""
    try:
        result = run_pipeline(audio_path, passage.strip())
    except Exception as e:  # keep the demo alive if the model/network hiccups
        msg = ("⚠️ Couldn't reach the analysis model. Check the connection and try again.\n\n"
               f"<sub>{type(e).__name__}: {e}</sub>")
        return msg, None, [], [], "", ""

    m = result["metrics"]
    metrics_md = (
        "### Results\n"
        f"**{m['wpm']} WPM**  ·  {m['accuracy_pct']}% words matched  ·  "
        f"{m['long_pauses']} long pauses  ·  {m['speech_seconds']}s speaking"
    )
    events_rows = [[e.word, e.type, f"{e.confidence:.2f}", e.evidence]
                   for e in result["events"]]
    return (metrics_md, render_waveform(audio_path, result), highlighted(result),
            events_rows, practice_plan_md(result), coach_script(result))


def analyze(audio_path: str | None, passage: str):
    """Streaming generator: shows a 'working' state immediately so a long analysis
    never looks frozen, then yields the results. Outputs order matches the button."""
    if not audio_path:
        yield "⚠️ Record or upload a reading first, or pick a previous one below.", None, [], [], "", ""
        return
    if not (passage and passage.strip()):
        yield "⚠️ Enter or pick a passage first — the text you're reading.", None, [], [], "", ""
        return
    yield (
        "### ⏳ Analyzing your reading…\n"
        "<sub>Transcribing, then Nemotron classifies each flagged moment and writes your "
        "plan. A brand-new clip can take up to ~90 seconds; cached clips are instant.</sub>",
        None, [], [], "", "",
    )
    yield _run_analysis(audio_path, passage)


def practice_plan_md(result) -> str:
    """Compose the 'Your practice plan' card from the planner + coaching content."""
    practice = result.get("practice")
    rec = result.get("recommendation")
    parts: list[str] = []
    if rec is not None and rec.problem_sound:
        moments = "moment" if rec.sound_count == 1 else "moments"
        parts.append(f"**What tripped you up:** *{rec.problem_sound}*-sounds "
                     f"({rec.sound_count} {moments})")
    if practice is not None:
        parts.append(f"**Try — {practice.exercise.replace('_', ' ')}:** {practice.feedback}")
    if rec is not None:
        parts.append(f"**Tongue twister:** {rec.tongue_twister}")
        parts.append(f"**Breathing:** {rec.breathing}")
        if rec.suggested_passage:
            parts.append(f"**Next passage to try:** {rec.suggested_passage.replace('_', ' ')} "
                         "(pick it from the passage list above)")
    return "### Your practice plan\n\n" + "\n\n".join(parts) if parts else ""


def coach_script(result) -> str:
    """A natural spoken coaching turn for ElevenLabs: numbers + the sound you caught
    on + a drill to imitate + a breath. Only mentions numbers from the metrics."""
    m = result["metrics"]
    practice = result.get("practice")
    rec = result.get("recommendation")
    parts: list[str] = []
    if practice is not None and practice.feedback:
        parts.append(practice.feedback)  # Nemotron's grounded coaching sentences
    else:
        parts.append(f"You read at {m['wpm']} words per minute, "
                     f"with {m['accuracy_pct']} percent of the words matching.")
    if rec is not None and rec.problem_sound:
        parts.append(f"One thing to focus on: your {rec.problem_sound} sounds.")
    if rec is not None:
        parts.append(f"Try this slowly, after me. {rec.tongue_twister}")
        parts.append(rec.breathing)
    parts.append("Take a breath, and give it another go.")
    return " ".join(parts)


# Pre-cached recordings, keyed by their dropdown label -> (wav path, passage id).
PREVIOUS = {label: (path, pid) for label, path, pid in demo_catalog()}


def on_passage_choice(choice: str) -> str:
    """Preset fills the box; 'Create your own' clears it so the user can type."""
    return "" if choice == CUSTOM_OPTION else load_passage(choice)


def analyze_previous(label: str):
    """Load a cached recording + passage and show its analysis (instant from cache).
    Returns [audio_in, passage_dd, passage_box, metrics, transcript, events, feedback]."""
    if not label or label not in PREVIOUS:
        return gr.update(), gr.update(), gr.update(), "", None, [], [], "", ""
    path, pid = PREVIOUS[label]
    passage = load_passage(pid)
    metrics_md, wave, hl, rows, fb, script = _run_analysis(path, passage)  # cached -> instant
    return path, pid, passage, metrics_md, wave, hl, rows, fb, script


with gr.Blocks(title="SpeakR") as demo:
    gr.Markdown("# 🎙️ SpeakR")
    gr.Markdown("### Read-aloud practice companion")
    gr.Markdown(f"<sub>{DISCLAIMER}</sub>")

    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            gr.Markdown("### 1 · Choose a passage")
            passage_dd = gr.Dropdown(
                choices=passage_ids() + [CUSTOM_OPTION], value=passage_ids()[0],
                label="Pick a preset, or “Create your own”",
            )
            passage_box = gr.Textbox(
                value=load_passage(passage_ids()[0]), label="Passage text",
                placeholder="Type or paste the passage you're going to read…", lines=8,
            )
        with gr.Column(scale=1):
            gr.Markdown("### 2 · Record or upload your reading")
            audio_in = gr.Audio(
                sources=["microphone", "upload"], type="filepath",
                label="🎙️ Record, or ⬆️ upload an audio file",
            )
            if PREVIOUS:
                prev_dd = gr.Dropdown(
                    choices=list(PREVIOUS.keys()), value=None,
                    label="▶ …or replay a previous recording (cached — instant)",
                )
            else:
                prev_dd = None

    run_btn = gr.Button("Analyze reading", variant="primary", size="lg")

    metrics_out = gr.Markdown()
    waveform_out = gr.Plot(label="Waveform")
    transcript_out = gr.HighlightedText(
        label="Transcript (colored where SpeakR flagged a moment)",
        color_map=EVENT_COLORS, show_legend=True,
    )
    events_out = gr.Dataframe(
        headers=["word", "type", "confidence", "evidence"],
        label="Detected moments", wrap=True,
    )
    feedback_out = gr.Markdown()
    coach_state = gr.State("")  # spoken-coach script from the latest analysis

    passage_dd.change(on_passage_choice, passage_dd, passage_box)
    run_btn.click(
        analyze, [audio_in, passage_box],
        [metrics_out, waveform_out, transcript_out, events_out, feedback_out, coach_state],
    )
    if prev_dd is not None:
        prev_dd.change(
            analyze_previous, prev_dd,
            [audio_in, passage_dd, passage_box, metrics_out, waveform_out,
             transcript_out, events_out, feedback_out, coach_state],
        )

    if VOICE_OK:
        gr.Markdown("### 🔊 Listen (ElevenLabs)")
        with gr.Row():
            coach_btn = gr.Button("🔊 Coach me", variant="primary")
            clone_btn = gr.Button("🎙️ Hear it in your own voice")
        voice_audio = gr.Audio(label="Playback", interactive=False, autoplay=True)

        # Spoken debrief: Nemotron writes it, ElevenLabs speaks it (feedback +
        # your problem sound + a drill to imitate).
        coach_btn.click(
            lambda script: voice.speak_feedback(script) if script else None,
            coach_state, voice_audio,
        )

        def clone_and_read(audio_path, passage):
            if not audio_path or not (passage and passage.strip()):
                gr.Warning("Add a recording and a passage first.")
                return None
            try:
                voice_id = voice.clone_voice([audio_path])
                return voice.fluent_playback(passage.strip(), voice_id)
            except Exception as e:  # slot limit / API hiccup — don't crash the demo
                gr.Warning(f"Voice clone unavailable right now ({type(e).__name__}).")
                return None

        clone_btn.click(clone_and_read, [audio_in, passage_box], voice_audio)

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="indigo"))
