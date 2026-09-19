from cadence import align as align_mod
from cadence import baseline, llm, mismatch
from cadence.enrich import build_enriched
from cadence.transcribe import transcribe
from cadence.vad import speech_regions
from cadence import config


def compute_metrics(words, aligned, regions, flags) -> dict:
    speech_time = sum(e - s for s, e in regions)
    matched = sum(1 for a in aligned if a.status == "matched")
    passage_len = sum(1 for a in aligned if a.status != "inserted")
    return {
        "wpm": round(len(words) / speech_time * 60) if speech_time else 0,
        "accuracy_pct": round(100 * matched / passage_len) if passage_len else 0,
        "long_pauses": sum(1 for f in flags if f.kind == "mid_phrase_silence"),
        "flag_count": len(flags),
        "speech_seconds": round(speech_time, 1),
    }


def run_pipeline(audio_path: str, passage: str, use_llm: bool = True) -> dict:
    words = transcribe(audio_path)
    aligned = align_mod.align(words, passage)
    regions = speech_regions(audio_path)
    flags = mismatch.find_flags(words, regions, aligned)
    enriched = build_enriched(words, aligned, flags, passage, regions)
    if use_llm:
        events = llm.judge(enriched)
    else:
        events = baseline.classify(flags, aligned, words)
    metrics = compute_metrics(words, aligned, regions, flags)
    practice = llm.plan(events, metrics) if use_llm else None
    return {
        "words": words, "aligned": aligned, "regions": regions,
        "flags": flags, "enriched": enriched, "events": events,
        "metrics": metrics, "practice": practice,
    }


def load_passage(passage_id: str) -> str:
    return (config.PASSAGES_DIR / f"{passage_id}.txt").read_text().strip()
