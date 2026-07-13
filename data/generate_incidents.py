"""Generate 60 synthetic incident reports: 40 corpus + 20 golden holdout."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Fault code -> canonical root cause (aligned with manuals + offline diagnoser)
CODE_CAUSE = {
    "E-102": "Seal jaw heater PID drift",
    "E-105": "Worn PTFE seal tape",
    "E-110": "Thermocouple lag on jaw B",
    "E-220": "Impeller cavitation from low NPSH",
    "E-AUDIO": "Bearing grease contamination",
    "E-225": "Coupling misalignment after maintenance",
    "E-310": "Outer race bearing spall",
    "E-312": "Fan blade imbalance from dust buildup",
    "E-315": "Loose pedestal bolts",
}

MACHINE_CODES = {
    "vffs_packager": ["E-102", "E-105", "E-110"],
    "centrifugal_pump": ["E-220", "E-AUDIO", "E-225"],
    "fan_unit": ["E-310", "E-312", "E-315"],
}

MACHINE_SYMPTOMS = {
    "vffs_packager": [
        "Seal jaw temperature deviation alarms",
        "Intermittent weak seals on pouch top",
        "E-102 flashing during changeover",
    ],
    "centrifugal_pump": [
        "High vibration RMS on pump skid",
        "Abnormal pump audio signature",
        "Flow instability with audible knock",
    ],
    "fan_unit": [
        "Rising acceleration peak on fan bearing",
        "Metallic ticking at 1x running speed",
        "E-310 bearing acceleration fault",
    ],
}


def build_incidents(seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows: list[dict] = []
    for i in range(1, 61):
        machine = rng.choice(list(MACHINE_CODES))
        code = rng.choice(MACHINE_CODES[machine])
        cause = CODE_CAUSE[code]
        symptom = rng.choice(MACHINE_SYMPTOMS[machine])
        if code not in symptom:
            symptom = f"{symptom} ({code})"
        ts = start + timedelta(days=i * 3, hours=rng.randint(0, 20))
        downtime = rng.randint(15, 180)
        rows.append(
            {
                "id": f"INC-{i:03d}",
                "timestamp": ts.isoformat(),
                "machine": machine,
                "fault_code": code,
                "symptom_description": symptom,
                "root_cause": cause,
                "resolution": f"Corrected {cause.lower()}; verified clear of {code}",
                "downtime_minutes": downtime,
                "manual_section_ids": [f"{machine}:{code}"],
                "split": "corpus" if i <= 40 else "golden",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/incidents"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = build_incidents(args.seed)
    corpus = [r for r in rows if r["split"] == "corpus"]
    golden = [r for r in rows if r["split"] == "golden"]
    (args.out / "incidents_corpus.json").write_text(
        json.dumps(corpus, indent=2), encoding="utf-8"
    )
    (args.out / "incidents_all.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    golden_path = Path("evals/golden_set.json")
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    golden_set = [
        {
            "id": r["id"],
            "machine": r["machine"],
            "fault_code": r["fault_code"],
            "symptom_description": r["symptom_description"],
            "expected_root_cause": r["root_cause"],
            "relevant_manual_section_ids": r["manual_section_ids"],
        }
        for r in golden
    ]
    golden_path.write_text(json.dumps(golden_set, indent=2), encoding="utf-8")
    print(f"wrote {len(corpus)} corpus, {len(golden)} golden")


if __name__ == "__main__":
    main()
