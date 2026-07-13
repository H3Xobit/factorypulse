"""Generate three synthetic equipment manuals as PDFs (reportlab)."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

MANUALS = [
    {
        "doc_id": "manual_vffs",
        "machine": "vffs_packager",
        "title": "Vertical Form-Fill-Seal Packaging Machine Manual",
        "faults": [
            ("E-102", "Seal jaw temperature deviation", "Check heater SSR, PID tune, thermocouple"),
            ("E-105", "Film tracking offset", "Inspect dancer rollers and edge sensor"),
            ("E-110", "Jaw pressure low", "Verify pneumatic regulator and jaw bushings"),
        ],
        "parts": ["HJ-220 heater cartridge", "TC-K-jaw thermocouple", "PTFE-25 seal tape"],
    },
    {
        "doc_id": "manual_fan",
        "machine": "fan_unit",
        "title": "Industrial Fan Unit Manual",
        "faults": [
            ("E-310", "Bearing acceleration peak", "Replace DE bearing; check alignment"),
            ("E-312", "Overcurrent on VFD", "Inspect blade fouling and inlet screen"),
            ("E-315", "Imbalance alarm", "Clean blades; rebalance to ISO G6.3"),
        ],
        "parts": ["6208-2RS bearing", "Fan pedestal bolt M16", "VFD filter kit"],
    },
    {
        "doc_id": "manual_pump",
        "machine": "centrifugal_pump",
        "title": "Centrifugal Pump Unit Manual",
        "faults": [
            ("E-220", "Pump vibration RMS above limit", "Check NPSH, impeller, coupling"),
            ("E-AUDIO", "Abnormal acoustic signature", "Inspect cavitation and bearing grease"),
            ("E-225", "Seal flush failure", "Restore flush flow; replace mechanical seal"),
        ],
        "parts": ["Impeller A-145", "Coupling spider CX-40", "Grease NLGI-2 EP"],
    },
]


def _sections(meta: dict) -> list[tuple[str, str, str]]:
    """Return (section_id, title, body) tuples."""
    out: list[tuple[str, str, str]] = []
    machine = meta["machine"]
    out.append(
        (
            f"{machine}:overview",
            "1. Overview",
            f"{meta['title']}. Rated for continuous packaging-line duty. "
            "Follow lockout/tagout before any intrusive maintenance.",
        )
    )
    out.append(
        (
            f"{machine}:safety",
            "2. Safety",
            "Isolate energy sources. Wear hearing protection near rotating equipment. "
            "Do not bypass interlocks during production.",
        )
    )
    for code, name, steps in meta["faults"]:
        body = (
            f"Fault code {code}: {name}. Troubleshooting: {steps}. "
            f"Related spare parts: {', '.join(meta['parts'])}."
        )
        out.append((f"{machine}:{code}", f"3. Fault {code}", body))
    out.append(
        (
            f"{machine}:maintenance",
            "4. Preventive maintenance",
            "Daily: listen for abnormal noise. Weekly: vibration spot check. "
            "Monthly: inspect fasteners, lubrication, and seals.",
        )
    )
    # Pad to ~15+ pages worth of content blocks
    for i in range(1, 12):
        out.append(
            (
                f"{machine}:proc-{i:02d}",
                f"5.{i} Operating procedure block {i}",
                "Confirm setpoints, verify sensors respond, record values in the shift log, "
                "and escalate to maintenance if fault codes reappear within 30 minutes. "
                + ("Detail paragraph. " * 18),
            )
        )
    return out


def write_manual(path: Path, meta: dict) -> list[dict]:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=LETTER)
    story = []
    story.append(Paragraph(meta["title"], styles["Title"]))
    story.append(Paragraph(f"Document ID: {meta['doc_id']}", styles["Normal"]))
    story.append(Spacer(1, 12))
    chunks: list[dict] = []
    for section_id, title, body in _sections(meta):
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(body, styles["BodyText"]))
        story.append(Spacer(1, 8))
        fault_code = section_id.split(":")[-1] if section_id.count(":") else None
        if fault_code and not fault_code.startswith("E-"):
            fault_code = None
        chunks.append(
            {
                "doc_id": meta["doc_id"],
                "section_id": section_id,
                "source_type": "manual",
                "machine": meta["machine"],
                "fault_code": fault_code if (fault_code or "").startswith("E-") else None,
                "title": title,
                "body": body,
            }
        )
        if "Fault" in title:
            story.append(PageBreak())
    # troubleshooting table
    data = [["Code", "Description", "Action"]] + [list(r) for r in meta["faults"]]
    table = Table(data, colWidths=[70, 200, 220])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(Paragraph("Troubleshooting table", styles["Heading2"]))
    story.append(table)
    for _ in range(6):
        story.append(PageBreak())
        story.append(Paragraph("Appendix notes", styles["Heading2"]))
        story.append(
            Paragraph(
                "Keep calibration certificates with the equipment history file. "
                + ("Appendix filler. " * 40),
                styles["BodyText"],
            )
        )
    doc.build(story)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/manuals"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    all_chunks: list[dict] = []
    for meta in MANUALS:
        pdf = args.out / f"{meta['doc_id']}.pdf"
        chunks = write_manual(pdf, meta)
        all_chunks.extend(chunks)
        print("wrote", pdf)
    import json

    (args.out / "manual_chunks.json").write_text(
        json.dumps(all_chunks, indent=2), encoding="utf-8"
    )
    print("chunks", len(all_chunks))


if __name__ == "__main__":
    main()
