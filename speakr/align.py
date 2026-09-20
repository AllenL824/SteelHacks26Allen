from dataclasses import dataclass
from difflib import SequenceMatcher

from speakr.transcribe import Word, normalize


@dataclass
class AlignedWord:
    status: str                 # "matched" | "substituted" | "inserted" | "skipped"
    passage_index: int | None   # None for inserted
    passage_word: str | None
    word: Word | None           # None for skipped


def align(words: list[Word], passage: str) -> list[AlignedWord]:
    passage_words = passage.split()
    a = [normalize(w.text) for w in words]
    b = [normalize(p) for p in passage_words]
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    out: list[AlignedWord] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append(AlignedWord("matched", j1 + k, passage_words[j1 + k], words[i1 + k]))
        elif tag == "replace":
            n = min(i2 - i1, j2 - j1)
            for k in range(n):
                out.append(AlignedWord("substituted", j1 + k, passage_words[j1 + k], words[i1 + k]))
            for k in range(i1 + n, i2):
                out.append(AlignedWord("inserted", None, None, words[k]))
            for k in range(j1 + n, j2):
                out.append(AlignedWord("skipped", k, passage_words[k], None))
        elif tag == "delete":
            for k in range(i1, i2):
                out.append(AlignedWord("inserted", None, None, words[k]))
        elif tag == "insert":
            for k in range(j1, j2):
                out.append(AlignedWord("skipped", k, passage_words[k], None))
    return out
