import sys

from cadence.vad import speech_regions

for s, e in speech_regions(sys.argv[1]):
    print(f"{s:6.2f} -> {e:6.2f}  ({e - s:.2f}s)")
