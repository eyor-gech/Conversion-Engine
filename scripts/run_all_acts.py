"""
Full five-act pipeline runner.
Outputs every artifact to results/ at the repo root.
MOCK_MODE must be false (set in .env).
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ── resolve base and set env BEFORE any project imports ──────────────────────
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE / ".env", override=True)
except Exception:
    pass

os.environ["MOCK_MODE"] = "false"
os.environ.setdefault("PYTHONPATH", str(BASE))


def _purge_mock_cache() -> int:
    """
    Remove all [MOCK:...] LLM entries from the disk cache so subsequent calls
    go to the real OpenRouter API instead of returning stale mock responses.
    Also resets the in-process cache and OpenRouter client singletons.
    Returns the number of entries purged.
    """
    cache_path = BASE / "data" / "cache_store.json"
    if not cache_path.exists():
        return 0
    try:
        data: dict = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    cleaned = {
        k: v for k, v in data.items()
        if not (isinstance(v, dict) and "[MOCK:" in str(v.get("text", "")))
    }
    removed = len(data) - len(cleaned)
    if removed > 0:
        cache_path.write_text(json.dumps(cleaned, indent=2, default=str), encoding="utf-8")

    # Reset singletons so they reload from the purged disk cache
    try:
        import core.cache as _cc
        _cc._GLOBAL_CACHE = None
    except Exception:
        pass
    try:
        import llm.openrouter_client as _oc
        _oc._CLIENT = None
    except Exception:
        pass
    return removed


_purged = _purge_mock_cache()
if _purged:
    print(f"[cache] Purged {_purged} stale mock entries — live OpenRouter calls will be made.")


RESULTS = BASE / "results"
RESULTS.mkdir(exist_ok=True)


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save(name: str, data: object) -> Path:
    p = RESULTS / name
    if isinstance(data, (dict, list)):
        p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    else:
        p.write_text(str(data), encoding="utf-8")
    return p


def _copy_if_exists(src: Path, dst_name: str) -> None:
    if src.exists():
        shutil.copy2(src, RESULTS / dst_name)


# ─────────────────────────────────────────────────────────────────────────────
# ACT I — tau2-bench dev-slice evaluation (30 tasks, real LLM via OpenRouter)
# ─────────────────────────────────────────────────────────────────────────────
async def act_i() -> dict:
    print("\n" + "=" * 60)
    print("ACT I — tau2-bench dev evaluation (30 tasks)")
    print("=" * 60)
    t0 = time.perf_counter()

    from eval.run_dev import run_dev_eval

    eval_out = RESULTS / "act1"
    eval_out.mkdir(exist_ok=True)
    score = await run_dev_eval(eval_out)

    # write baseline narrative
    from eval.run_dev import _write_baseline
    _write_baseline(BASE, score)
    _copy_if_exists(BASE / "baseline.md", "act1_baseline.md")

    elapsed = round(time.perf_counter() - t0, 1)
    score["elapsed_sec"] = elapsed
    _save("act1_score.json", score)
    print(f"  pass@1: {score.get('pass_at_1_mean')}  CI: {score.get('pass_at_1_ci_95')}  cost: ${score.get('cost_per_run_usd')}  [{elapsed}s]")
    return score


# ─────────────────────────────────────────────────────────────────────────────
# ACT II — production enrichment + outreach + CRM + booking (real APIs)
# ─────────────────────────────────────────────────────────────────────────────
async def act_ii() -> dict:
    print("\n" + "=" * 60)
    print("ACT II — production enrichment, outreach, CRM, booking")
    print("=" * 60)
    t0 = time.perf_counter()

    from agent.orchestrator import run_single_synthetic_thread

    act2_out = RESULTS / "act2"
    act2_out.mkdir(exist_ok=True)

    thread = await run_single_synthetic_thread(output_dir=act2_out)

    # Also run interactions latency benchmark (5 prospects to keep runtime sane)
    print("  Running interaction latency benchmark (5 prospects)…")
    from eval.run_interactions import run_many
    interactions = await run_many(num_prospects=5, output_dir=act2_out)

    result = {"thread": thread, "interactions": interactions}
    elapsed = round(time.perf_counter() - t0, 1)
    result["elapsed_sec"] = elapsed
    _save("act2_result.json", result)
    _copy_if_exists(act2_out / "sample_thread.json", "act2_sample_thread.json")
    _copy_if_exists(act2_out / "interaction_metrics.json", "act2_interaction_metrics.json")

    # hiring_signal_brief and competitor_gap_brief if emitted
    _copy_if_exists(BASE / "hiring_signal_brief.json", "act2_hiring_signal_brief.json")
    _copy_if_exists(BASE / "competitor_gap_brief.json", "act2_competitor_gap_brief.json")

    print(f"  Thread complete. Elapsed: {elapsed}s")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ACT III — 30 adversarial probes (real LLM classification)
# ─────────────────────────────────────────────────────────────────────────────
async def act_iii() -> dict:
    print("\n" + "=" * 60)
    print("ACT III — 30 adversarial probes")
    print("=" * 60)
    t0 = time.perf_counter()

    from eval.probe_runner import replay_probe_library

    probe_out = RESULTS / "act3_probe_results.json"
    result = await replay_probe_library(
        probe_path=BASE / "probes" / "probe_cases.json",
        output_path=probe_out,
    )
    elapsed = round(time.perf_counter() - t0, 1)
    result["elapsed_sec"] = elapsed
    # overwrite with elapsed added
    probe_out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    rates = result.get("trigger_rate_by_category", {})
    print(f"  Probes run: {result.get('total_probes')}  Elapsed: {elapsed}s")
    for cat, rate in sorted(rates.items()):
        print(f"    {cat}: trigger_rate={rate:.2f}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ACT IV — held-out evaluation + ablations (real LLM)
# ─────────────────────────────────────────────────────────────────────────────
async def act_iv() -> dict:
    print("\n" + "=" * 60)
    print("ACT IV — held-out evaluation + ablations")
    print("=" * 60)
    t0 = time.perf_counter()

    from eval.run_heldout import run

    act4_out = RESULTS / "act4"
    act4_out.mkdir(exist_ok=True)
    summary = await run(act4_out)

    elapsed = round(time.perf_counter() - t0, 1)
    summary["elapsed_sec"] = elapsed
    _save("act4_heldout_summary.json", summary)

    _copy_if_exists(BASE / "held_out_traces.jsonl", "act4_held_out_traces.jsonl")
    _copy_if_exists(BASE / "ablation_results.json", "act4_ablation_results.json")
    _copy_if_exists(BASE / "invoice_summary.json", "act4_invoice_summary.json")

    print(f"  held-out pass@1: {summary.get('pass_at_1')}  CI: {summary.get('ci_95')}  [{elapsed}s]")
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# ACT V — evidence graph + decision memo PDF
# ─────────────────────────────────────────────────────────────────────────────
def act_v() -> dict:
    print("\n" + "=" * 60)
    print("ACT V — evidence graph + decision memo")
    print("=" * 60)
    t0 = time.perf_counter()

    # generate_evidence reads from eval/ and root-level artifacts
    # We need to ensure it can find the score files the other acts wrote.
    # Copy back key files it expects in eval/ if needed.
    eval_dir = BASE / "eval"
    eval_dir.mkdir(exist_ok=True)
    for src, dst in [
        (RESULTS / "act1" / "score_log.json",       eval_dir / "score_log.json"),
        (RESULTS / "act4" / "heldout_summary.json",  eval_dir / "heldout_summary.json"),
    ]:
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    import importlib.util, types
    spec = importlib.util.spec_from_file_location("gen_ev", BASE / "eval" / "generate_evidence.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.main()

    from memo.build_memo import main as build_memo
    build_memo()

    elapsed = round(time.perf_counter() - t0, 1)
    _copy_if_exists(BASE / "evidence_graph.json",  "act5_evidence_graph.json")
    _copy_if_exists(BASE / "memo" / "memo.pdf",    "act5_memo.pdf")
    _copy_if_exists(BASE / "memo" / "memo.md",     "act5_memo.md")

    evidence = {}
    ev_path = BASE / "evidence_graph.json"
    if ev_path.exists():
        evidence = json.loads(ev_path.read_text(encoding="utf-8"))

    print(f"  Evidence graph and memo written. [{elapsed}s]")
    return {"evidence": evidence, "elapsed_sec": elapsed}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
async def main() -> None:
    run_start = _stamp()
    summary: dict[str, object] = {
        "run_started_at": run_start,
        "mock_mode": os.environ.get("MOCK_MODE"),
        "acts": {},
    }

    acts = [
        ("act_i",   "Act I  — tau2 dev eval",              act_i),
        ("act_ii",  "Act II — production thread",           act_ii),
        ("act_iii", "Act III — adversarial probes",         act_iii),
        ("act_iv",  "Act IV  — held-out eval + ablations",  act_iv),
    ]

    for key, label, fn in acts:
        try:
            result = await fn()
            summary["acts"][key] = {"status": "ok", "result": result}
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"\n  ERROR in {label}:\n{tb}")
            summary["acts"][key] = {"status": "error", "error": str(exc), "traceback": tb}

    # Act V is synchronous
    try:
        result_v = act_v()
        summary["acts"]["act_v"] = {"status": "ok", "result": result_v}
    except Exception as exc:
        tb = traceback.format_exc()
        print(f"\n  ERROR in Act V:\n{tb}")
        summary["acts"]["act_v"] = {"status": "error", "error": str(exc), "traceback": tb}

    summary["run_finished_at"] = _stamp()

    # Write master summary
    _save("run_summary.json", summary)

    print("\n" + "=" * 60)
    print("ALL ACTS COMPLETE")
    print(f"Results written to: {RESULTS}")
    print("=" * 60)
    for key, info in summary["acts"].items():
        status = info.get("status", "?")
        icon = "[OK]" if status == "ok" else "[ERR]"
        print(f"  {icon} {key}: {status}")

    print(f"\nrun_summary.json -> {RESULTS / 'run_summary.json'}")


if __name__ == "__main__":
    asyncio.run(main())
