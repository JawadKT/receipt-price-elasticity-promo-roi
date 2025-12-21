"""Run the full synthetic pipeline end-to-end.

From the project root:

    python src/run_all.py

This will:
1) Detect price changes and promotions
2) Estimate product-level price elasticity (where data allows)
3) Simulate promo ROI scenarios

Outputs are written under `reports/tables/`.
"""

from __future__ import annotations

from pathlib import Path

import subprocess
import sys


def _run(cmd: list[str]) -> int:
    """Run a subprocess command, streaming output.

    Returns the process return code.
    """

    print("\n>>>", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    # Ensure commands run from repo root so relative paths line up
    cmds = [
        [sys.executable, str(repo_root / "src" / "run_price_change_detection.py")],
        [sys.executable, str(repo_root / "src" / "run_elasticity.py")],
        [sys.executable, str(repo_root / "src" / "run_promo_simulation.py")],
    ]

    for cmd in cmds:
        code = _run(cmd)
        if code != 0:
            print(f"Command failed with code {code}: {' '.join(cmd)}")
            sys.exit(code)

    print("\nPipeline completed successfully.")
    print("Key outputs:")
    print("  - reports/tables/price_change_events.csv")
    print("  - reports/tables/elasticity_estimates.csv")
    print("  - reports/tables/promo_scenarios.csv")


if __name__ == "__main__":
    main()
