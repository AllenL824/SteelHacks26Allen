"""All experiments -> eval/results.md. Run: python -m eval.run_eval [--quick]"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from speakr import config, llm
from speakr.llm import Event
from speakr.pipeline import load_passage, run_pipeline


def match_events(predicted: list[Event], labels: list[dict],
                 tol: float = config.MATCH_TOLERANCE):
    """Match by type + time overlap (intervals padded by tol). Greedy, one label per prediction."""
    used: set[int] = set()
    tp, fp = [], []
    for p in sorted(predicted, key=lambda e: e.start):
        hit = None
        for i, l in enumerate(labels):
            if i in used or p.type != l["type"]:
                continue
            if p.start <= l["end"] + tol and p.start >= l["start"] - tol:
                hit = i
                break
        if hit is None:
            fp.append(p)
        else:
            used.add(hit)
            tp.append(p)
    fn = [l for i, l in enumerate(labels) if i not in used]
    return tp, fp, fn


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def judge_plain(words, passage: str) -> list[Event]:
    """Experiment 4 arm: judge sees only the plain transcript, no enrichment."""
    plain = f"PASSAGE: {passage}\n\nTRANSCRIPT: " + " ".join(w.text for w in words)
    raw = llm.cached_chat(
        [{"role": "system", "content": llm.JUDGE_SYSTEM},
         {"role": "user", "content": plain}],
        tag="judge_plain",
    )
    return [e for e in llm.parse_events(raw) if e.type != "false_alarm"]


def evaluate(dataset_dir: Path, quick: bool = False) -> dict:
    manifest = json.loads((dataset_dir / "labels.json").read_text())
    if quick:
        manifest = manifest[:4]
    counts = {arm: defaultdict(lambda: [0, 0, 0]) for arm in ("judge", "baseline", "plain")}
    fluent_fp = {"judge": 0, "baseline": 0}
    fluent_clips = 0
    failures = []
    for m in manifest:
        passage = load_passage(m["passage"])
        clip = str(dataset_dir / m["clip"])
        print(f"eval {m['clip']} ...")
        res_judge = run_pipeline(clip, passage, use_llm=True)
        res_base = run_pipeline(clip, passage, use_llm=False)
        plain_events = judge_plain(res_judge["words"], passage)
        arms = {"judge": res_judge["events"], "baseline": res_base["events"],
                "plain": plain_events}
        if not m["events"]:
            fluent_clips += 1
            fluent_fp["judge"] += len(arms["judge"])
            fluent_fp["baseline"] += len(arms["baseline"])
        for arm, events in arms.items():
            tp, fp, fn = match_events(events, m["events"])
            for e in tp:
                counts[arm][e.type][0] += 1
            for e in fp:
                counts[arm][e.type][1] += 1
            for l in fn:
                counts[arm][l["type"]][2] += 1
            if arm == "judge" and (fp or fn) and len(failures) < 4:
                failures.append({
                    "clip": m["clip"],
                    "missed": [l["type"] for l in fn],
                    "spurious": [(e.type, e.start) for e in fp],
                })
    return {"counts": counts, "fluent_fp": fluent_fp,
            "fluent_clips": fluent_clips, "failures": failures,
            "n_clips": len(manifest)}


def render(results: dict, name: str) -> str:
    lines = [f"## Dataset: {name} ({results['n_clips']} clips)", ""]
    for arm in ("judge", "baseline", "plain"):
        lines.append(f"### {arm}")
        lines.append("| type | P | R | F1 | tp/fp/fn |")
        lines.append("|---|---|---|---|---|")
        totals = [0, 0, 0]
        for etype, (tp, fp, fn) in sorted(results["counts"][arm].items()):
            p, r, f1 = prf(tp, fp, fn)
            lines.append(f"| {etype} | {p:.2f} | {r:.2f} | {f1:.2f} | {tp}/{fp}/{fn} |")
            totals = [totals[0] + tp, totals[1] + fp, totals[2] + fn]
        p, r, f1 = prf(*totals)
        lines.append(f"| **overall** | {p:.2f} | {r:.2f} | {f1:.2f} | {'/'.join(map(str, totals))} |")
        lines.append("")
    if results["fluent_clips"]:
        lines.append(f"False alarms on {results['fluent_clips']} fluent clips: "
                     f"judge={results['fluent_fp']['judge']}, "
                     f"baseline={results['fluent_fp']['baseline']}")
        lines.append("")
    if results["failures"]:
        lines.append("### Failure cases")
        for f in results["failures"]:
            lines.append(f"- `{f['clip']}`: missed {f['missed']}, spurious {f['spurious']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    quick = "--quick" in sys.argv
    out = ["# SpeakR evaluation results", ""]
    for name in ("synthetic", "real"):
        d = config.DATA_DIR / name
        if (d / "labels.json").exists():
            out.append(render(evaluate(d, quick=quick), name))
    report = "\n".join(out)
    (config.ROOT / "eval" / "results.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
