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
    "Cadence is a practice companion, not a diagnostic or treatment tool. "
    "It highlights moments in a recording to practice with — it does not assess "
    "or diagnose any condition. Demo clips are pre-recorded."
)


def passage_ids() -> list[str]:
    return sorted(p.stem for p in config.PASSAGES_DIR.glob("*.txt"))


def demo_clips() -> list[str]:
    d = config.DATA_DIR / "demo"
    return sorted(str(p) for p in d.glob("*.wav")) if d.exists() else []


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


def analyze(audio_path: str | None, passage_id: str):
    if not audio_path:
        return [], [], "Record or upload a clip first.", ""
    passage = load_passage(passage_id)
    result = run_pipeline(audio_path, passage)
    events_rows = [[e.word, e.type, f"{e.confidence:.2f}", e.evidence]
                   for e in result["events"]]
    m = result["metrics"]
    metrics_md = (f"**{m['wpm']} WPM** · {m['accuracy_pct']}% words matched · "
                  f"{m['long_pauses']} long pauses · {m['speech_seconds']}s speaking")
    feedback = ""  # planner arrives in Task 7
    return highlighted(result), events_rows, metrics_md, feedback


with gr.Blocks(title="Cadence") as demo:
    gr.Markdown("# Cadence — read-aloud practice companion")
    gr.Markdown(f"*{DISCLAIMER}*")
    with gr.Row():
        passage_dd = gr.Dropdown(choices=passage_ids(), value=passage_ids()[0],
                                 label="Passage")
        audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath",
                            label="Read the passage aloud")
    passage_text = gr.Markdown(load_passage(passage_ids()[0]))
    passage_dd.change(lambda pid: load_passage(pid), passage_dd, passage_text)

    demo_dd = gr.Dropdown(choices=demo_clips(), label="…or pick a demo clip")
    demo_dd.change(lambda p: p, demo_dd, audio_in)

    run_btn = gr.Button("Analyze", variant="primary")
    metrics_out = gr.Markdown()
    transcript_out = gr.HighlightedText(label="Transcript", color_map=EVENT_COLORS)
    events_out = gr.Dataframe(headers=["word", "type", "confidence", "evidence"],
                              label="Detected moments")
    feedback_out = gr.Markdown(label="Practice suggestion")

    run_btn.click(analyze, [audio_in, passage_dd],
                  [transcript_out, events_out, metrics_out, feedback_out])

if __name__ == "__main__":
    demo.launch()
