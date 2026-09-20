"""Generate labeled synthetic clips: fluent `say` reading + pydub-inserted disfluencies.

Local-only: macOS `say` + ffmpeg. No API keys. Labels are exact because we
insert at known positions and track cumulative offset.
"""
import json
import random
import subprocess
from pathlib import Path

from pydub import AudioSegment

from speakr import config
from speakr.transcribe import Word, transcribe

OUT_DIR = config.DATA_DIR / "synthetic"
VOICES = ["Samantha", "Daniel", "Karen", "Moira"]  # substitute if not installed
CLIPS_PER_PASSAGE_VOICE = 2   # 2 passages x 4 voices x 2 = 16 clips
FLUENT_FRACTION = 0.2         # ~20% untouched
EVENTS_PER_CLIP = (1, 2)      # min, max inserted events
rng = random.Random(42)


def synth_fluent(text: str, voice: str, out_wav: Path) -> None:
    aiff = out_wav.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff),
         "-ar", "16000", "-ac", "1", str(out_wav)],
        check=True,
    )
    aiff.unlink()


def ms(seconds: float) -> int:
    return int(seconds * 1000)


def insert_block(audio: AudioSegment, at_ms: int) -> tuple[AudioSegment, int]:
    dur = rng.randint(1000, 2000)
    silence = AudioSegment.silent(duration=dur, frame_rate=audio.frame_rate)
    return audio[:at_ms] + silence + audio[at_ms:], dur


def insert_sound_repetition(audio: AudioSegment, at_ms: int) -> tuple[AudioSegment, int]:
    head = audio[at_ms:at_ms + 80]                      # first ~80ms of the word
    n = rng.randint(2, 3)
    ins = AudioSegment.silent(duration=0, frame_rate=audio.frame_rate)
    for _ in range(n):
        gap = AudioSegment.silent(duration=rng.randint(50, 90), frame_rate=audio.frame_rate)
        ins += head + gap
    return audio[:at_ms] + ins + audio[at_ms:], len(ins)


def insert_prolongation(audio: AudioSegment, at_ms: int) -> tuple[AudioSegment, int]:
    head = audio[at_ms:at_ms + 150]                     # first ~150ms
    factor = rng.randint(3, 4)
    stretched = head
    for _ in range(factor - 1):                         # crossfade-loop ~= prolongation
        stretched = stretched.append(head, crossfade=min(40, len(head) // 2))
    extra = len(stretched) - 150
    return audio[:at_ms] + stretched + audio[at_ms + 150:], extra


INSERTERS = {
    "block": insert_block,
    "sound_repetition": insert_sound_repetition,
    "prolongation": insert_prolongation,
}


def eligible_words(words: list[Word]) -> list[tuple[int, Word]]:
    # skip the first word, want words long enough to grab a head from
    return [(i, w) for i, w in enumerate(words) if i > 0 and (w.end - w.start) >= 0.2]


def make_clip(fluent: AudioSegment, words: list[Word], clip_name: str) -> tuple[AudioSegment, list[dict]]:
    n_events = rng.randint(*EVENTS_PER_CLIP)
    candidates = eligible_words(words)
    if len(candidates) < n_events:
        return fluent, []
    chosen = sorted(rng.sample(candidates, n_events), key=lambda c: c[1].start)
    audio = fluent
    labels: list[dict] = []
    offset = 0
    for word_index, word in chosen:
        etype = rng.choice(list(INSERTERS))
        at = ms(word.start) + offset
        audio, inserted = INSERTERS[etype](audio, at)
        labels.append({
            "type": etype,
            "word_index": word_index,
            "start": at / 1000,
            "end": (at + inserted) / 1000,
        })
        offset += inserted
    return audio, labels


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    passages = sorted(config.PASSAGES_DIR.glob("*.txt"))
    for passage_path in passages:
        text = passage_path.read_text().strip()
        for voice in VOICES:
            fluent_wav = OUT_DIR / f"fluent_{passage_path.stem}_{voice}.wav"
            print(f"synth {fluent_wav.name}")
            synth_fluent(text, voice, fluent_wav)
            words = transcribe(str(fluent_wav))
            fluent = AudioSegment.from_wav(fluent_wav)
            for k in range(CLIPS_PER_PASSAGE_VOICE):
                name = f"{passage_path.stem}_{voice}_{k}.wav"
                if rng.random() < FLUENT_FRACTION:
                    audio, labels = fluent, []
                else:
                    audio, labels = make_clip(fluent, words, name)
                audio.export(OUT_DIR / name, format="wav")
                manifest.append({"clip": name, "passage": passage_path.stem, "events": labels})
                print(f"  wrote {name}: {[e['type'] for e in labels] or 'fluent'}")
            fluent_wav.unlink()
    (OUT_DIR / "labels.json").write_text(json.dumps(manifest, indent=2))
    total = sum(len(m["events"]) for m in manifest)
    print(f"\n{len(manifest)} clips, {total} labeled events -> {OUT_DIR / 'labels.json'}")


if __name__ == "__main__":
    main()
