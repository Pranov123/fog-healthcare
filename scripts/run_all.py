from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fogsim.experiments import run_all  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full MobiCare-Fog experiment suite.")
    parser.add_argument("--outdir", default="results", help="output directory for CSV results")
    parser.add_argument("--quick", action="store_true", help="shorter runs with fewer points")
    args = parser.parse_args()
    run_all(args.outdir, quick=args.quick)


if __name__ == "__main__":
    main()
