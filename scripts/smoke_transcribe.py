import sys

from cadence.align import align
from cadence.transcribe import transcribe
from cadence import config

audio = sys.argv[1]
passage = (config.PASSAGES_DIR / "rainbow.txt").read_text().strip()
words = transcribe(audio)
for w in words[:10]:
    print(f"{w.start:6.2f} {w.end:6.2f}  {w.text}")
print("---")
for a in align(words, passage):
    if a.status != "matched":
        print(a.status, a.passage_word, a.word.text if a.word else None)
