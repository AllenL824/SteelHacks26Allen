from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PASSAGES_DIR = DATA_DIR / "passages"
CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# ASR
WHISPER_MODEL = "small"          # drop to "base" if transcription > ~15s per clip
WHISPER_COMPUTE = "int8"
# Prime the transcriber to keep disfluencies (fillers, stutters) instead of
# tidying them into fluent text — sound/word repetitions must survive to be detected.
FILLER_PROMPT = ("Umm, so, uh, I- I was like, you know, well... "
                 "b-b-ball, s-s-sun, the the the, wh-what, c-c-came, p-p-please.")
# Off = don't let Whisper smooth each segment against the previous one; preserves
# repeated sounds/words (e.g. "s-s-sun") that context-conditioning would normalize away.
WHISPER_CONDITION_ON_PREVIOUS = False

# Mismatch thresholds
SECONDS_PER_SYLLABLE = 0.22      # expected duration per syllable
MIN_EXPECTED_DURATION = 0.15     # floor for 1-syllable words
STRETCH_RATIO = 2.0              # word is "stretched" if dur > ratio * expected
GAP_THRESHOLD = 0.8              # mid-phrase silence if gap before word > this
REGION_WORD_OVERLAP = 0.05       # seconds of overlap for a word to "explain" a VAD region
SENTENCE_END = ".!?;:"           # gap after these chars is not mid-phrase

# Eval
MATCH_TOLERANCE = 0.3            # seconds; predicted event matches label if same type + intervals (padded by this) overlap

# LLM
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NEMOTRON_MODEL = "nvidia/nemotron-3-super-120b-a12b"  # llama-3.3-nemotron-super-49b-v1.5 reached EOL 2026-08-26; this is the current "Super" tier successor per https://integrate.api.nvidia.com/v1/models
LLM_TEMPERATURE = 0.2
