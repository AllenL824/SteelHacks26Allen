import gradio as gr

from cadence import config
from cadence.pipeline import load_passage, run_pipeline
from cadence.reader import (
    DEFAULT_WPM, JS_RESET, JS_START, JS_STOP, MAX_WPM, MIN_WPM,
    READER_CSS, READER_JS, render_reader, wrong_words,
)

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
    """Returns (metrics_md, reader_html, highlighted, events_rows, feedback_md) —
    order matches the outputs list on the Analyze button. `passage` is the raw text
    the reader read (a preset or their own custom passage). The reader HTML is left
    untouched (gr.update()) on errors so the passage stays readable."""
    if not audio_path:
        return ("⚠️ Record or upload a reading first, or pick a previous one below.",
                gr.update(), [], [], "")
    if not (passage and passage.strip()):
        return "⚠️ Enter or pick a passage first — the text you're reading.", gr.update(), [], [], ""
    try:
        result = run_pipeline(audio_path, passage.strip())
    except Exception as e:  # keep the demo alive if the model/network hiccups
        msg = ("⚠️ Couldn't reach the analysis model. Check the connection and try again.\n\n"
               f"<sub>{type(e).__name__}: {e}</sub>")
        return msg, gr.update(), [], [], ""

    m = result["metrics"]
    metrics_md = (
        "### Results\n"
        f"**{m['wpm']} WPM**  ·  {m['accuracy_pct']}% words matched  ·  "
        f"{m['long_pauses']} long pauses  ·  {m['speech_seconds']}s speaking"
    )
    events_rows = [[e.word, e.type, f"{e.confidence:.2f}", e.evidence]
                   for e in result["events"]]
    reader_html = render_reader(passage.strip(), wrong_words(result["aligned"]), done=True)
    return metrics_md, reader_html, highlighted(result), events_rows, practice_plan_md(result)


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


READER_LEGEND = (
    '<div class="cr-legend">'
    '<span class="sw" style="background:#f97316"></span>follow the orange highlight while you read'
    '&nbsp;&nbsp;·&nbsp;&nbsp;'
    '<span class="sw" style="background:#dc2626"></span>after analysis, misread or skipped words turn red'
    '</div>'
)


# Pre-cached recordings, keyed by their dropdown label -> (wav path, passage id).
PREVIOUS = {label: (path, pid) for label, path, pid in demo_catalog()}


def on_passage_choice(choice: str):
    """Preset fills the box + reader; 'Create your own' clears the box to type into."""
    text = "" if choice == CUSTOM_OPTION else load_passage(choice)
    return text, render_reader(text)


def sync_reader(passage: str):
    """Re-render the guided reader whenever the passage text changes."""
    return render_reader(passage or "")


def analyze_previous(label: str):
    """Load a cached recording + passage and show its analysis (instant from cache).
    Returns [audio_in, passage_dd, passage_box, reader_out, metrics, transcript, events, feedback]."""
    if not label or label not in PREVIOUS:
        return (gr.update(), gr.update(), gr.update(), gr.update(), "", [], [], "")
    path, pid = PREVIOUS[label]
    passage = load_passage(pid)
    metrics_md, reader_html, hl, rows, fb = analyze(path, passage)
    return path, pid, passage, reader_html, metrics_md, hl, rows, fb


# Gradio 6 moved css/head from Blocks() to launch(); support both.
_GRADIO_6 = int(gr.__version__.split(".")[0]) >= 6
PAGE_KWARGS = {"css": READER_CSS, "head": READER_JS}
LAUNCH_KWARGS = {"theme": gr.themes.Soft(primary_hue="indigo")}
if _GRADIO_6:
    LAUNCH_KWARGS.update(PAGE_KWARGS)

with gr.Blocks(title="SpeakR", **({} if _GRADIO_6 else PAGE_KWARGS)) as demo:
    gr.Markdown("# 🎙️ SpeakR")
    gr.Markdown("### Read-aloud practice companion")
    gr.Markdown(f"<sub>{DISCLAIMER}</sub>")

    _default_passage = load_passage(passage_ids()[0])
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            gr.Markdown("**1. Choose a passage**")
            passage_dd = gr.Dropdown(
                choices=passage_ids() + [CUSTOM_OPTION], value=passage_ids()[0],
                label="Pick a preset, or “Create your own”", container=True,
            )
            passage_box = gr.Textbox(
                value=_default_passage, label="Passage text",
                placeholder="Type or paste the passage you're going to read…", lines=3,
            )
            reader_out = gr.HTML(render_reader(_default_passage))
            gr.HTML(READER_LEGEND)
            with gr.Row():
                pace = gr.Slider(MIN_WPM, MAX_WPM, value=DEFAULT_WPM, step=5,
                                 label="Pace (words per minute)", scale=3)
                start_btn = gr.Button("▶ Start guide", size="sm", scale=1)
                stop_btn = gr.Button("■ Stop", size="sm", scale=1)
        with gr.Column(scale=1):
            gr.Markdown("**2. Record or upload your reading**")
            gr.Markdown("<sub>The guide starts on its own when you hit record.</sub>")
            audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                label="🎙️ Record, or ⬆️ upload an audio file")

    prev_dd = None
    if PREVIOUS:
        prev_dd = gr.Dropdown(
            choices=list(PREVIOUS.keys()), value=None,
            label="▶ Analyze a previous recording (cached — loads instantly)",
        )

    # Passage text drives the reader. Preset/custom selection updates both;
    # typing a custom passage re-renders the reader too.
    passage_dd.change(on_passage_choice, passage_dd, [passage_box, reader_out]
                      ).then(None, None, None, js=JS_RESET)
    passage_box.change(sync_reader, passage_box, reader_out).then(None, None, None, js=JS_RESET)

    # Reading guide: runs in the browser only, no round-trip to the server.
    audio_in.start_recording(None, [pace], None, js=JS_START)
    audio_in.stop_recording(None, None, None, js=JS_STOP)
    audio_in.clear(None, None, None, js=JS_RESET)
    start_btn.click(None, [pace], None, js=JS_START)
    stop_btn.click(None, None, None, js=JS_STOP)

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

    # Stop the guide first so it doesn't paint over the red results.
    run_btn.click(None, None, None, js=JS_STOP).then(
        analyze, [audio_in, passage_box],
        [metrics_out, reader_out, transcript_out, events_out, feedback_out],
    )

    if prev_dd is not None:
        prev_dd.change(
            analyze_previous, prev_dd,
            [audio_in, passage_dd, passage_box, reader_out,
             metrics_out, transcript_out, events_out, feedback_out],
        ).then(None, None, None, js=JS_STOP)

if __name__ == "__main__":
    demo.launch(**LAUNCH_KWARGS)
