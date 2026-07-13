"""Eval harness for diagnosis, retrieval, hallucination, latency."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from factorypulse.graph.build import run_diagnosis
from factorypulse.rag.retrieve import retrieve


def fuzzy_score(expected: str, predicted: str) -> float:
    el = expected.lower().strip()
    pl = predicted.lower().strip()
    if not el or not pl:
        return 0.0
    if el == pl or el in pl or pl in el:
        return 1.0
    e = set(el.split())
    p = set(pl.split())
    overlap = len(e & p) / max(len(e | p), 1)
    if overlap >= 0.45:
        return 1.0
    if overlap >= 0.25:
        return 0.5
    return 0.0


def run(smoke_n: int | None = None) -> dict:
    golden = json.loads(Path("evals/golden_set.json").read_text(encoding="utf-8"))
    if smoke_n:
        golden = golden[:smoke_n]
    scores = []
    retr_hits = []
    halluc = []
    latencies = []
    for case in golden:
        query = f"{case['fault_code']} {case['symptom_description']}"
        t0 = time.time()
        manuals = retrieve(query, source_type="manual", top_k=5)
        result = run_diagnosis(
            {
                "machine": case["machine"],
                "symptom": case["symptom_description"],
                "fault_code": case["fault_code"],
            }
        )
        latencies.append(time.time() - t0)
        pred = (result.get("diagnosis") or {}).get("root_cause") or ""
        scores.append(fuzzy_score(case["expected_root_cause"], pred))
        relevant = set(case.get("relevant_manual_section_ids") or [])
        got = {h["section_id"] for h in manuals}
        retr_hits.append(len(relevant & got) / max(len(relevant), 1))
        evidence = (result.get("diagnosis") or {}).get("evidence") or []
        all_hits = retrieve(query, source_type=None, top_k=10)
        valid = {h["section_id"] for h in all_hits}
        bad = sum(1 for ev in evidence if ev.get("section_id") not in valid)
        halluc.append(bad / max(len(evidence), 1))

    def avg(xs: list[float]) -> float:
        return sum(xs) / max(len(xs), 1)

    lat_sorted = sorted(latencies)
    p50 = lat_sorted[len(lat_sorted) // 2] if lat_sorted else 0.0
    p95 = lat_sorted[int(len(lat_sorted) * 0.95)] if lat_sorted else 0.0
    return {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "n": len(golden),
        "diagnosis_accuracy": avg(scores),
        "retrieval_precision_at_5": avg(retr_hits),
        "hallucination_rate": avg(halluc),
        "latency_p50_s": p50,
        "latency_p95_s": p95,
        "cost_per_report_usd": 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", type=int, default=10)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    result = run(smoke_n=None if args.full else args.smoke)
    out_dir = Path("evals/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{stamp}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["diagnosis_accuracy"] < 0.7:
        raise SystemExit("diagnosis_accuracy below 0.7")
    if result["hallucination_rate"] > 0.05:
        raise SystemExit("hallucination_rate above 0.05")


if __name__ == "__main__":
    main()
