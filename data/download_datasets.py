"""Dataset fetch helpers (MIMII / NASA IMS). Prefer running off this workstation.

Uses Kaggle when KAGGLE_USERNAME/KAGGLE_KEY are set. Large archives are
gitignored under data/audio/. Delete local downloads after use.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

BEARING_KAGGLE = "vinayak123tyagi/bearing-dataset"
MIMII_ZENODO = "https://zenodo.org/records/3384388"


def kaggle_download(dataset: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if not (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")):
        raise RuntimeError(
            "Set KAGGLE_USERNAME and KAGGLE_KEY, or download manually from Kaggle"
        )
    subprocess.check_call(
        ["kaggle", "datasets", "download", "-d", dataset, "-p", str(out), "--unzip"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/audio"))
    parser.add_argument("--bearing", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level="INFO")
    readme = args.out / "README_DATASETS.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "\n".join(
            [
                "# Dataset download notes",
                "",
                f"- MIMII: {MIMII_ZENODO}",
                f"- NASA IMS bearings (Kaggle): `{BEARING_KAGGLE}`",
                "",
                "Simulator synthetic audio/sensors keep demos offline without these archives.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if args.bearing:
        kaggle_download(BEARING_KAGGLE, args.out / "bearing")
        logger.info("downloaded bearing dataset to %s", args.out / "bearing")
    logger.info("wrote %s", readme)


if __name__ == "__main__":
    main()
