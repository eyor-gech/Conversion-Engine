from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from agent.orchestrator import run_single_synthetic_thread


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> None:
    base = Path(__file__).resolve().parents[1]

    # Act I
    py = sys.executable
    _run([py, "eval/run_dev.py", "--output-dir", "eval"], base)

    # Act II
    asyncio.run(run_single_synthetic_thread(base))
    _run([py, "eval/run_interactions.py", "--num-prospects", "20", "--output-dir", "eval"], base)

    # Act III
    _run(
        [
            py,
            "eval/probe_runner.py",
            "--probe-file",
            "probes/probe_cases.json",
            "--output-file",
            "eval/probe_results.json",
        ],
        base,
    )

    # Act IV
    _run([py, "eval/run_heldout.py", "--output-dir", "eval"], base)

    # Act V
    _run([py, "eval/generate_evidence.py"], base)
    _run([py, "memo/build_memo.py"], base)

    print(json.dumps({"status": "complete", "root": str(base)}, indent=2))


if __name__ == "__main__":
    main()
