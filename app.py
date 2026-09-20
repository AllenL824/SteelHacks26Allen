import gradio as gr

from cadence import config
from cadence.pipeline import load_passage, run_pipeline

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


def analyze(audio_path: str | None, passage: str):
    """Returns (metrics_md, highlighted, events_rows, feedback_md) — order matches
    the outputs list on the Analyze button. `passage` is the raw text read."""
    if not audio_path:
        return "⚠️ Record or upload a reading first, or pick a previous one below.", [], [], ""
    if not (passage and passage.strip()):
        return "⚠️ Enter or pick a passage first — the text you're reading.", [], [], ""
    try:
        result = run_pipeline(audio_path, passage.strip())
    except Exception as e:  # keep the demo alive if the model/network hiccups
        msg = ("⚠️ Couldn't reach the analysis model. Check the connection and try again.\n\n"
               f"<sub>{type(e).__name__}: {e}</sub>")
        return msg, [], [], ""

    m = result["metrics"]
    metrics_md = (
        "### Results\n"
        f"**{m['wpm']} WPM**  ·  {m['accuracy_pct']}% words matched  ·  "
        f"{m['long_pauses']} long pauses  ·  {m['speech_seconds']}s speaking"
    )
    events_rows = [[e.word, e.type, f"{e.confidence:.2f}", e.evidence]
                   for e in result["events"]]
    return metrics_md, highlighted(result), events_rows, practice_plan_md(result)


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


# Pre-cached recordings, keyed by their dropdown label -> (wav path, passage id).
PREVIOUS = {label: (path, pid) for label, path, pid in demo_catalog()}


def on_passage_choice(choice: str) -> str:
    """Preset fills the box; 'Create your own' clears it so the user can type."""
    return "" if choice == CUSTOM_OPTION else load_passage(choice)


def analyze_previous(label: str):
    """Load a cached recording + passage and show its analysis (instant from cache).
    Returns [audio_in, passage_dd, passage_box, metrics, transcript, events, feedback]."""
    if not label or label not in PREVIOUS:
        return gr.update(), gr.update(), gr.update(), "", [], [], ""
    path, pid = PREVIOUS[label]
    passage = load_passage(pid)
    metrics_md, hl, rows, fb = analyze(path, passage)
    return path, pid, passage, metrics_md, hl, rows, fb


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
    transcript_out = gr.HighlightedText(
        label="Transcript (colored where SpeakR flagged a moment)",
        color_map=EVENT_COLORS, show_legend=True,
    )
    events_out = gr.Dataframe(
        headers=["word", "type", "confidence", "evidence"],
        label="Detected moments", wrap=True,
    )
    feedback_out = gr.Markdown()

    passage_dd.change(on_passage_choice, passage_dd, passage_box)
    run_btn.click(analyze, [audio_in, passage_box],
                  [metrics_out, transcript_out, events_out, feedback_out])
    if prev_dd is not None:
        prev_dd.change(
            analyze_previous, prev_dd,
            [audio_in, passage_dd, passage_box,
             metrics_out, transcript_out, events_out, feedback_out],
        )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="indigo"))
