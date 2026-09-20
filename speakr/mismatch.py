from dataclasses import dataclass

from speakr import config
from speakr.align import AlignedWord
from speakr.transcribe import Word, normalize

VOWELS = "aeiouy"


@dataclass
class Flag:
    kind: str               # "unexplained_sound" | "stretched_word" | "mid_phrase_silence" | "repetition"
    start: float
    end: float
    word_index: int | None  # index into the transcript word list, None for regions
    detail: str


def syllable_count(word: str) -> int:
    word = normalize(word)
    count, prev_vowel = 0, False
    for c in word:
        is_vowel = c in VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    return max(count, 1)


def expected_duration(word: str) -> float:
    return max(syllable_count(word) * config.SECONDS_PER_SYLLABLE,
               config.MIN_EXPECTED_DURATION)


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def find_flags(
    words: list[Word],
    regions: list[tuple[float, float]],
    aligned: list[AlignedWord],
) -> list[Flag]:
    flags: list[Flag] = []

    # 0. Repetitions. Whisper renders stutters as repeated tokens ("the the the")
    #    or cut-off fragments ("s-", "th-"), often separated by bare "-" tokens.
    #    Detect these first so we can suppress the stretched_word flag on the same
    #    words (a repeated word is a repetition, not a prolongation).
    rep_indices: set[int] = set()
    # (a) runs of identical consecutive content words, skipping empty tokens like "-"
    content = [(i, normalize(w.text)) for i, w in enumerate(words) if normalize(w.text)]
    c = 0
    while c < len(content):
        d = c
        while d + 1 < len(content) and content[d + 1][1] == content[c][1]:
            d += 1
        if d > c:  # >=2 identical tokens in a row
            i0, i1 = content[c][0], content[d][0]
            for idx, _ in content[c:d + 1]:
                rep_indices.add(idx)
            flags.append(Flag("repetition", words[i0].start, words[i1].end, i0,
                              f"'{words[i0].text}' repeated {d - c + 1}x"))
        c = d + 1
    # (b) cut-off fragments: a token whose original text contains "-" but has letters
    for i, w in enumerate(words):
        if i not in rep_indices and "-" in w.text and normalize(w.text):
            rep_indices.add(i)
            flags.append(Flag("repetition", w.start, w.end, i,
                              f"cut-off fragment '{w.text}' (sound repetition)"))

    # 1. Speech region with no overlapping word -> unexplained_sound
    for r0, r1 in regions:
        if not any(_overlap(r0, r1, w.start, w.end) >= config.REGION_WORD_OVERLAP for w in words):
            flags.append(Flag("unexplained_sound", r0, r1, None,
                              f"speech from {r0:.2f}-{r1:.2f}s with no transcribed word"))

    # 2. Word duration far beyond expected -> stretched_word
    #    (skip words already explained by a repetition flag)
    for i, w in enumerate(words):
        if i in rep_indices:
            continue
        dur = w.end - w.start
        exp = expected_duration(w.text)
        if dur > config.STRETCH_RATIO * exp:
            flags.append(Flag("stretched_word", w.start, w.end, i,
                              f"'{w.text}' took {dur:.2f}s, expected ~{exp:.2f}s"))

    # 3. Long gap before a word, not after sentence punctuation -> mid_phrase_silence
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        prev = words[i - 1].text
        if gap > config.GAP_THRESHOLD and not (prev and prev[-1] in config.SENTENCE_END):
            flags.append(Flag("mid_phrase_silence", words[i - 1].end, words[i].start, i,
                              f"{gap:.2f}s silence before '{words[i].text}'"))

    return sorted(flags, key=lambda f: f.start)
