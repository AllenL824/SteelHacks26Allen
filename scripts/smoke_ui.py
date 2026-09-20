"""Launch the Gradio UI with the ASR/LLM pipeline stubbed out.

Lets you check layout and the reading guide without whisper/torch installed:
    .venv\\Scripts\\python scripts\\smoke_ui.py            # opens on :7860
    .venv\\Scripts\\python scripts\\smoke_ui.py --check    # start, fetch /, exit
"""
import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from speakr import config  # noqa: E402


def _fake_run_pipeline(audio_path: str, passage: str, use_llm: bool = True) -> dict:
    words = passage.split()
    t = 0.0
    tw, aligned = [], []
    for i, p in enumerate(words):
        if i == 3:  # pretend the reader skipped this word
            aligned.append(SimpleNamespace(status="skipped", passage_index=i, passage_word=p, word=None))
            continue
        said = "banana" if i == 7 else p
        w = SimpleNamespace(text=said, start=t, end=t + 0.3)
        t += 0.4
        tw.append(w)
        status = "substituted" if said != p else "matched"
        aligned.append(SimpleNamespace(status=status, passage_index=i, passage_word=p, word=w))
    events = [SimpleNamespace(word=tw[1].text, start=tw[1].start, type="word_repetition",
                              confidence=0.8, evidence="stub")]
    return {
        "words": tw, "aligned": aligned, "events": events,
        "metrics": {"wpm": 120, "accuracy_pct": 90, "long_pauses": 1,
                    "flag_count": 2, "speech_seconds": round(t, 1)},
        "practice": None, "recommendation": None,
    }


fake = types.ModuleType("speakr.pipeline")
fake.run_pipeline = _fake_run_pipeline
fake.load_passage = lambda pid: (config.PASSAGES_DIR / f"{pid}.txt").read_text().strip()
sys.modules["speakr.pipeline"] = fake

import app  # noqa: E402

if __name__ == "__main__":
    if "--check" in sys.argv:
        import urllib.request
        _, url, _ = app.demo.launch(prevent_thread_lock=True, quiet=True, **app.LAUNCH_KWARGS)
        page = urllib.request.urlopen(url, timeout=10).read().decode()
        assert "speakrReader" in page, "reader script missing from page head"
        assert "cr-cur" in page, "reader css missing from page"
        print("ok", url)
        app.demo.close()
    else:
        app.demo.launch(**app.LAUNCH_KWARGS)
