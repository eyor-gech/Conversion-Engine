from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from agent.core.orchestrator import build_orchestrator
from agent.intelligence.hiring_brief import generate_hiring_brief
from agent.intelligence.insight_engine import build_insight_packet
from agent.outreach.email_generator import generate_email
from agent.outreach.sms_generator import generate_sms
from agent.outreach.tone_guardrail import apply_tone_guardrail
from agent.outreach.validator import validate_outreach
from eval.runner_wrapper import run_tau2_dev_slice_sync
from pipelines.enrichment.signal_pipeline import run_signal_pipeline
from pipelines.ingestion.crunchbase_loader import load_companies
from pipelines.ingestion.job_scraper import load_job_snapshot
from pipelines.ingestion.layoffs_loader import load_layoff_flags


def _write_baseline(path: Path, score: dict[str, object]) -> None:
    content = (
        "# Act I Baseline\n\n"
        f"- pass@1: {score['pass_at_1']}\n"
        f"- latency p50: {score['latency_ms_p50']} ms\n"
        f"- latency p95: {score['latency_ms_p95']} ms\n"
        f"- estimated cost/run: ${score['estimated_cost_usd']}\n"
        f"- tasks: {score['task_count']}\n"
        f"- trials: {score['trials']}\n"
        "- sealed set executed: false\n"
    )
    path.write_text(content, encoding="utf-8")


def run_act_i(output_dir: Path) -> dict[str, object]:
    score = run_tau2_dev_slice_sync(task_count=30, trials=5, output_dir=output_dir)
    _write_baseline(output_dir / "baseline.md", score)
    return score


async def run_act_ii(output_dir: Path) -> dict[str, object]:
    os.environ.setdefault("MOCK_MODE", "true")
    orchestrator = build_orchestrator()

    companies = load_companies(orchestrator.paths.data_dir / "sample_companies.json")
    job_baselines = load_job_snapshot(orchestrator.paths.data_dir / "jobs_snapshot.json")
    layoffs_map = load_layoff_flags(orchestrator.paths.data_dir / "layoffs.csv")
    company = companies[0]
    company.layoffs_reported = layoffs_map.get(
        company.company_id,
        layoffs_map.get(company.name.lower(), company.layoffs_reported),
    )

    scored = run_signal_pipeline(company, job_baselines.get(company.company_id, len(company.open_roles)), orchestrator.settings.icp_threshold)
    insights = build_insight_packet(scored, companies)
    hiring_brief = generate_hiring_brief(company, scored.signals)
    email = generate_email(scored, insights)
    email.body = apply_tone_guardrail(email.body)
    sms = generate_sms(scored)
    validation = validate_outreach(email, scored)

    crm = await orchestrator.hubspot.upsert_contact(
        email=f"partnerships@{company.domain}",
        name=f"{company.name} Partnerships",
        company=company.name,
    )
    deal = await orchestrator.hubspot.create_deal(company=company.name, stage="contacted", amount=15000)
    booking = await orchestrator.calcom.create_booking(attendee_email=f"partnerships@{company.domain}", slot_iso="2026-04-30T11:00:00Z")
    sent_email = await orchestrator.resend.send_email(
        to_email=f"partnerships@{company.domain}",
        subject=email.subject or f"Hello {company.name}",
        body=email.body,
    )
    sent_sms = await orchestrator.sms.send_sms(to_number="+254700000000", message=sms.body)

    result = {
        "mock_mode": True,
        "company_id": company.company_id,
        "icp_segment": scored.icp_segment,
        "ai_maturity_score": scored.ai_maturity_score,
        "hiring_signal_brief": hiring_brief,
        "competitor_gap": insights["competitor_gap"],
        "email_validation": validation.model_dump(),
        "email": sent_email,
        "sms": sent_sms,
        "hubspot_contact": crm,
        "hubspot_deal": deal,
        "calcom_booking": booking,
    }
    (output_dir / "act2_log.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Five-Act driver for Act I + Act II reproducible runs")
    parser.add_argument("--act", choices=["all", "act1", "act2"], default="all")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {}
    if args.act in {"all", "act1"}:
        payload["act1"] = run_act_i(out_dir)
    if args.act in {"all", "act2"}:
        import asyncio

        payload["act2"] = asyncio.run(run_act_ii(out_dir))
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
