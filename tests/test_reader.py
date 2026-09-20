from types import SimpleNamespace

from cadence.reader import READER_ID, render_reader, wrong_words


def aligned(status, passage_index, said=None):
    word = SimpleNamespace(text=said) if said is not None else None
    return SimpleNamespace(status=status, passage_index=passage_index, word=word)


def test_render_wraps_each_word_in_indexed_span():
    html = render_reader("The quick fox.")
    assert f'id="{READER_ID}"' in html
    assert '<span class="cr-w" data-i="0">The</span>' in html
    assert '<span class="cr-w" data-i="2">fox.</span>' in html
    assert html.count("cr-w") == 3
    assert "cr-wrong" not in html and "cr-read" not in html


def test_render_marks_wrong_words_red_with_tooltip():
    html = render_reader("The quick fox", wrong={1: 'You said "slow"'}, done=True)
    assert 'class="cr-w cr-wrong" data-i="1" title="You said &quot;slow&quot;"' in html
    # every other word is tinted as already read
    assert 'class="cr-w cr-read" data-i="0"' in html
    assert 'class="cr-w cr-read" data-i="2"' in html


def test_render_escapes_html_in_passage():
    html = render_reader("a <b> & c")
    assert "<b>" not in html
    assert "&lt;b&gt;" in html and "&amp;" in html


def test_wrong_words_from_alignment():
    result = [
        aligned("matched", 0, "the"),
        aligned("substituted", 1, "slow"),
        aligned("inserted", None, "um"),
        aligned("skipped", 2),
        aligned("matched", 3, "fox"),
    ]
    wrong = wrong_words(result)
    assert set(wrong) == {1, 2}
    assert "slow" in wrong[1]
    assert wrong[2] == "Skipped"
