from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from agent.core.orchestrator import build_orchestrator

app = FastAPI(title="Conversion Engine", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run/{mode}")
async def run_engine(mode: Literal["interim", "final"]) -> JSONResponse:
    orchestrator = build_orchestrator()
    report = await orchestrator.run(mode)
    trace_path = orchestrator.paths.base_dir / "trace_log.json"
    orchestrator.export_traces(trace_path)
    return JSONResponse(content=report.model_dump(mode="json"))


@app.get("/traces")
async def traces() -> JSONResponse:
    path = Path(__file__).resolve().parent / "trace_log.json"
    if not path.exists():
        return JSONResponse(content={"events": []})
    return JSONResponse(content={"events": json.loads(path.read_text(encoding="utf-8"))})


def cli() -> None:
    parser = argparse.ArgumentParser(description="Run Conversion Engine demo flow")
    parser.add_argument("--mode", choices=["interim", "final"], default="interim")
    args = parser.parse_args()

    orchestrator = build_orchestrator()

    import asyncio

    report = asyncio.run(orchestrator.run(args.mode))
    orchestrator.export_traces(orchestrator.paths.base_dir / "trace_log.json")
    print(json.dumps(report.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    cli()
