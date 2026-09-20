"""Guided-reading view: the passage as individually addressable words.

While the user records, a small script in the page walks an orange highlight
across the words at a chosen pace (a paced-reading guide). After analysis the
same view is re-rendered with misread or skipped words in red.

This module has no heavy imports so it can be unit-tested without the ASR stack.
"""
import html

READER_ID = "cadence-reader"

DEFAULT_WPM = 130
MIN_WPM, MAX_WPM = 60, 220


def render_reader(passage: str, wrong: dict[int, str] | None = None,
                  done: bool = False) -> str:
    """HTML for the reader. `wrong` maps passage word index -> tooltip text;
    those words render red. With `done=True` every other word is tinted as read."""
    wrong = wrong or {}
    spans = []
    for i, word in enumerate(passage.split()):
        classes = ["cr-w"]
        title = ""
        if i in wrong:
            classes.append("cr-wrong")
            title = f' title="{html.escape(wrong[i], quote=True)}"'
        elif done:
            classes.append("cr-read")
        spans.append(f'<span class="{" ".join(classes)}" data-i="{i}"{title}>'
                     f'{html.escape(word)}</span>')
    return f'<div id="{READER_ID}" class="cr">{" ".join(spans)}</div>'


def wrong_words(aligned) -> dict[int, str]:
    """Passage indices the reader got wrong (substituted or skipped), with a
    hover explanation. Inserted words have no passage position, so they are
    left to the transcript view."""
    out: dict[int, str] = {}
    for a in aligned:
        if a.passage_index is None:
            continue
        if a.status == "substituted":
            out[a.passage_index] = f"You said “{a.word.text}”"
        elif a.status == "skipped":
            out[a.passage_index] = "Skipped"
    return out


READER_CSS = f"""
#{READER_ID} {{
  font-size: 1.35rem; line-height: 1.95; padding: 1rem 1.25rem;
  border: 1px solid var(--border-color-primary); border-radius: var(--radius-lg);
  background: var(--background-fill-secondary);
}}
#{READER_ID} .cr-w {{
  padding: 0 .12em; border-radius: .3em;
  transition: background-color .15s ease, color .15s ease;
}}
#{READER_ID} .cr-read {{ color: #c2410c; }}
#{READER_ID} .cr-cur {{ background: #f97316; color: #fff; font-weight: 600; }}
#{READER_ID} .cr-wrong {{
  color: #dc2626; font-weight: 600; cursor: help;
  text-decoration: underline wavy #dc2626; text-decoration-thickness: 2px;
  text-underline-offset: .15em;
}}
.cr-legend {{ font-size: .85rem; opacity: .8; }}
.cr-legend .sw {{
  display: inline-block; width: .9em; height: .9em; border-radius: .2em;
  vertical-align: -.1em; margin-right: .3em;
}}
"""

# Runs in the page. Words are looked up fresh on every tick so the guide keeps
# working after the passage is re-rendered, and simply stops at the end.
READER_JS = f"""
<script>
window.cadenceReader = (() => {{
  let timer = null, idx = -1;
  const words = () => Array.from(document.querySelectorAll('#{READER_ID} .cr-w'));
  function paint() {{
    words().forEach((el, i) => {{
      el.classList.toggle('cr-read', i < idx);
      el.classList.toggle('cr-cur', i === idx);
    }});
  }}
  // Time on a word scales with its length, with a breath after punctuation.
  function msFor(el, wpm) {{
    const base = 60000 / Math.max({MIN_WPM}, Math.min({MAX_WPM}, wpm));
    const t = el.textContent.trim();
    const letters = t.replace(/[^A-Za-z0-9']/g, '').length;
    let ms = base * Math.min(2.2, Math.max(0.6, letters / 5));
    if (/[.!?;:]["')]*$/.test(t)) ms += base * 0.9;
    else if (/,["')]*$/.test(t)) ms += base * 0.4;
    return ms;
  }}
  function step(wpm) {{
    const ws = words();
    idx += 1;
    if (idx >= ws.length) {{ idx = ws.length; paint(); timer = null; return; }}
    paint();
    timer = setTimeout(() => step(wpm), msFor(ws[idx], wpm));
  }}
  return {{
    start(wpm) {{
      this.stop();
      words().forEach(el => el.classList.remove('cr-wrong', 'cr-read', 'cr-cur'));
      idx = -1;
      step(Number(wpm) || {DEFAULT_WPM});
    }},
    stop() {{ if (timer) clearTimeout(timer); timer = null; }},
    reset() {{ this.stop(); idx = -1; paint(); }},
  }};
}})();
</script>
"""

# js= snippets for Gradio event listeners. Gradio passes the listener's input
# values as arguments and ignores the return value when there are no outputs.
JS_START = "(wpm) => { window.cadenceReader.start(wpm); }"
JS_STOP = "() => { window.cadenceReader.stop(); }"
JS_RESET = "() => { window.cadenceReader.reset(); }"
