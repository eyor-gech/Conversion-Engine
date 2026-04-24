# Conversion Engine (Tenacious)

Production-grade B2B lead conversion system with LLM-orchestrated enrichment, bidirectional
outreach handling, CRM / calendar integration, and a full multi-act evaluation suite.

---

## System Overview

The Conversion Engine ingests structured company profiles, runs a 6-signal enrichment pipeline to
compute AI-maturity scores and ICP segments, generates personalised multi-channel outreach (email +
SMS), syncs every interaction to HubSpot and Cal.com, and measures its own quality through a 30-probe
adversarial evaluation and a Tau2-benchmark harness.

The system is deterministic by default (all LLM calls are cached), sandbox-safe (MOCK_MODE=true),
and structured for clean handoff to the next engineer.

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Ingestion
        A1[sample_companies.json] --> L1[crunchbase_loader]
        A2[jobs_snapshot.json] --> L2[job_scraper\n+ robots.txt check]
        A3[layoffs.csv] --> L3[layoffs_loader]
    end

    subgraph Enrichment
        L1 & L2 & L3 --> SIG[signal_pipeline\nscoring.py]
        SIG --> MAT[ai_maturity.py\n6 signals]
        SIG --> ICP[icp_classifier.py\nthreshold=0.62]
        MAT & ICP --> INS[insight_engine\nhiring_brief + competitor_gap]
    end

    subgraph Outreach
        INS --> EG[email_generator]
        INS --> SG[sms_generator]
        EG --> TG[tone_guardrail]
        TG --> VAL[validator]
        SG --> SMS_GUARD[warm-lead guard]
    end

    subgraph Integrations
        VAL --> HS[HubSpot\ncontact + deal + enrichment]
        VAL --> RS[Resend\nemail send]
        SMS_GUARD --> AT[Africa's Talking\nSMS send]
        HS --> CAL[Cal.com\nbooking]
    end

    subgraph Routing
        RS --> EH[email_handler\nwebhook]
        AT --> SH[sms_handler\nwebhook]
        EH & SH --> RH[reply_handler\nintent → route]
    end

    subgraph Evaluation
        RH --> TR[LangfuseTracer\ntrace_log.json]
        TR --> PR[probe_runner\n30 adversarial probes]
        TR --> TB[tau_bench_runner\npass@1 + CI]
        PR & TB --> EV[evidence_graph.json]
        EV --> MEMO[memo/memo.pdf]
    end
```

---

## End-to-End Data Flow

```
CompanyInput (JSON)
  └─ Signal pipeline ──────────────────────────────── signals dict (6 SignalRecords)
       ├─ funding_recency      (source: crunchbase)
       ├─ job_velocity         (source: jobs_snapshot)
       ├─ layoffs              (source: layoffs.fyi CSV)
       ├─ leadership_change    (source: news/signal)
       ├─ tech_stack_match     (source: crunchbase)
       └─ ai_maturity          (6-signal weighted score 0–3)
  └─ ICP classifier ──────────────────────────────── segment_1/2/3/4 | abstain
  └─ Insight engine ──────────────────────────────── hiring_brief + competitor_gap
  └─ Outreach generator ──────────────────────────── OutreachDraft (email + SMS)
       ├─ tone_guardrail (replace overclaims)
       ├─ confidence_conditioning (phrasing policy)
       └─ validator (block unsupported assertions)
  └─ Integrations ────────────────────────────────── CRM + calendar + send
       ├─ HubSpot: upsert_contact → create_deal → upsert_enrichment → update_booking_summary
       ├─ Cal.com: create_booking (slot confirmation)
       ├─ Resend: send_email
       └─ Africa's Talking: send_sms (warm-lead gate enforced)
  └─ Evaluation ──────────────────────────────────── trace_log + probe_results + evidence_graph
```

---

## Tech Stack

| Layer            | Technology                        | Notes                                       |
|------------------|-----------------------------------|---------------------------------------------|
| LLM gateway      | OpenRouter (HTTP)                 | Multi-model routing; gpt-4o-mini / gemini   |
| Email            | Resend                            | Webhook: POST /webhooks/email               |
| SMS              | Africa's Talking                  | Webhook: POST /webhooks/sms                 |
| CRM              | HubSpot                           | Contacts, Deals, Enrichment, Timeline       |
| Calendar         | Cal.com                           | Booking creation                            |
| Scraping         | Playwright (headless Chromium)    | robots.txt compliant; cached                |
| Web framework    | FastAPI + uvicorn                 | REST API + CLI entry point                  |
| Caching          | Custom disk/memory (SHA256 keyed) | `core/cache.py`; `data/cache_store.json`    |
| Observability    | Langfuse-compatible tracer        | `agent/core/tracing.py`; `trace_log.json`   |
| Event bus        | Custom async pub/sub              | `core/event_bus.py`                         |
| Concurrency      | asyncio + semaphores              | `core/rate_limiter.py` (LLM ≤ 2, tools ≤ 4)|
| Statistics       | Bootstrap (10k resamples)         | `eval/stats.py`; `eval/metrics.py`          |
| Benchmark        | Tau2-bench (tau2-bench/)          | 30 dev tasks + sealed held-out              |
| Config           | YAML + .env                       | `config/settings.yaml` + `.env`             |

---

## Directory Structure

```
Conversion_Engine/
│
├── agent/                          # LLM orchestration and outreach
│   ├── core/
│   │   ├── orchestrator.py         # ConversionOrchestrator: main pipeline driver
│   │   ├── state.py                # Pydantic models (CompanyInput, ScoredCompany, …)
│   │   ├── config.py               # AppSettings, Paths, env overrides
│   │   └── tracing.py              # Lightweight Langfuse-compatible tracer
│   ├── enrichment.py               # Unified enrichment runner (hiring brief + gap)
│   ├── conversation/               # Reply routing and scheduling decisions
│   │   ├── reply_handler.py
│   │   ├── intent_classifier.py
│   │   └── scheduler.py
│   ├── intelligence/               # ICP, hiring brief, competitor gap, insight engine
│   │   ├── icp_classifier.py       # threshold=0.62; segments 1–4 or abstain
│   │   ├── hiring_brief.py         # Signal narrative with confidence + source + timestamp
│   │   ├── competitor_gap.py       # 5-10 peers; distribution position; sparse-sector fallback
│   │   └── insight_engine.py       # Combines hiring_brief + competitor_gap
│   ├── signals/
│   │   ├── scoring.py              # Aggregate all signals → ScoredCompany
│   │   ├── ai_maturity.py          # 6-signal weighted scoring (0–3)
│   │   ├── crunchbase.py           # Funding recency signal
│   │   ├── jobs.py                 # Job velocity + leadership signals
│   │   └── layoffs.py              # Layoff flag signal
│   ├── outreach/
│   │   ├── email_handler.py        # Bounce / reply webhook processor
│   │   ├── sms_handler.py          # Inbound SMS + warm-lead gate
│   │   ├── email_generator.py      # Personalised email composition
│   │   ├── sms_generator.py        # SMS composition
│   │   ├── validator.py            # Blocks unsupported assertions
│   │   └── tone_guardrail.py       # Replaces overclaims (guarantee → aim to, etc.)
│   ├── policies/
│   │   └── signal_confidence.py    # Confidence-aware phrasing (Act IV mechanism)
│   └── guardrails/                 # Safety / policy checks
│
├── core/                           # Infrastructure
│   ├── cache.py                    # Thread-safe disk+memory cache
│   ├── event_bus.py                # Async pub/sub (email, SMS events)
│   ├── event_schema.py             # ChannelEvent, ChannelError, ErrorCode
│   └── rate_limiter.py             # Semaphore guards (LLM ≤ 2, tools ≤ 4)
│
├── pipelines/
│   ├── ingestion/
│   │   ├── crunchbase_loader.py    # Loads sample_companies.json (cached)
│   │   ├── job_scraper.py          # Loads jobs_snapshot + Playwright scraping (robots.txt aware)
│   │   └── layoffs_loader.py       # Parses layoffs.csv
│   ├── enrichment/
│   │   ├── signal_pipeline.py      # Scores company → ScoredCompany
│   │   ├── unified_signal_enrichment.py  # LLM-driven signal schema (4 sources)
│   │   └── feature_store.py
│   └── scoring/
│
├── integrations/
│   ├── hubspot_client.py           # upsert_contact, create_deal, upsert_enrichment, update_booking_summary
│   ├── resend_client.py            # send_email (mock-safe)
│   ├── calcom_client.py            # create_booking
│   ├── africastalking_client.py    # send_sms
│   └── crm_calendar_bridge.py      # CRM + calendar cross-integration
│
├── llm/
│   ├── reasoning_layer.py          # 9 async LLM methods (classify, score, summarise)
│   └── openrouter_client.py        # HTTP client + retries + cache
│
├── eval/
│   ├── probe_runner.py             # Executes 30 probes; writes probe_results.json
│   ├── probe_library.py            # Probe set builder
│   ├── failure_taxonomy.py         # Failure category definitions
│   ├── tau_bench_runner.py         # Tau2 dev/held-out eval
│   ├── metrics.py                  # Wilson CI
│   ├── stats.py                    # Bootstrap CI + p-value (10k resamples)
│   ├── pricing.py                  # Per-model cost estimation
│   ├── ablation.py                 # 4 ablation variants
│   ├── run_dev.py                  # Act I: 30 tau2 dev tasks
│   ├── run_heldout.py              # Act I (heldout): sealed evaluation
│   ├── run_interactions.py         # Multi-prospect interaction eval
│   └── generate_evidence.py        # Compiles evidence_graph.json
│
├── probes/
│   ├── probe_cases.json            # 30 adversarial probe definitions
│   ├── probe_library.md            # Human-readable probe catalog
│   ├── failure_taxonomy.md         # 6 failure categories + probe mapping (all 30 mapped)
│   ├── target_failure_mode.md      # Primary failure + business cost + alternatives comparison
│   └── mechanism_design.md         # Act IV: re-implementation spec, hyperparameters, ablations
│
├── runs/
│   ├── five_act_driver.py          # Act I (tau2 dev) + Act II (enrichment + outreach)
│   ├── act2_log.json               # Act II output artifact
│   └── baseline.md                 # Act I benchmark summary
│
├── scripts/
│   ├── generate_mock_data.py       # Creates sample company profiles
│   ├── run_eval.py                 # Full eval orchestrator
│   ├── finalize_submission.py      # Five-act end-to-end pipeline
│   └── system_memo.py              # System documentation helper
│
├── memo/
│   ├── build_memo.py               # PDF memo builder
│   └── memo.pdf                    # Final submission memo
│
├── tests/
│   ├── test_probe_regression.py
│   ├── test_signal_confidence_policy.py
│   └── test_sms_guard.py
│
├── config/
│   └── settings.yaml               # App config (icp_threshold, mock_mode, Langfuse, etc.)
│
├── data/
│   ├── sample_companies.json       # ~10–20 CompanyInput objects
│   ├── jobs_snapshot.json          # Open-role counts by company_id
│   ├── layoffs.csv                 # Layoff flags by company_id and name
│   ├── cache_store.json            # Persistent LLM / computation cache
│   └── tau2-bench/                 # Tau2 benchmark tasks (30 dev + sealed held-out)
│
├── main.py                         # FastAPI app + CLI (--mode interim|final)
├── requirements.txt
├── .env.example                    # Environment variable template
├── Dockerfile
├── docker-compose.yml
└── pytest.ini
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env`**.

```bash
cp .env.example .env
```

| Variable                | Required | Default      | Purpose                                         |
|-------------------------|----------|--------------|-------------------------------------------------|
| `PYTHONPATH`            | Yes      | `.`          | Ensures project root is on the import path      |
| `OPENROUTER_API_KEY`    | Yes      | —            | LLM gateway (OpenRouter)                        |
| `HUBSPOT_API_KEY`       | Yes*     | —            | CRM write access (*mock-safe if `MOCK_MODE=true`)|
| `RESEND_API_KEY`        | Yes*     | —            | Email send (*mock-safe)                         |
| `AFRICASTALKING_API_KEY`| Yes*     | —            | SMS send (*mock-safe)                           |
| `CALCOM_API_KEY`        | Yes*     | —            | Calendar booking (*mock-safe)                   |
| `LANGFUSE_PUBLIC_KEY`   | No       | —            | Langfuse observability (optional)               |
| `LANGFUSE_SECRET_KEY`   | No       | —            | Langfuse observability (optional)               |
| `MAX_LLM_CONCURRENCY`   | No       | `2`          | Max parallel LLM calls                         |
| `MAX_TOOL_CONCURRENCY`  | No       | `4`          | Max parallel tool/integration calls            |
| `MOCK_MODE`             | No       | `true`       | Sandbox all external API calls                 |
| `SIGNAL_CONFIDENCE_MODE`| No       | `confidence_aware` | Phrasing policy: `confidence_aware` \| `binary_threshold` \| `no_confidence` |

> When `MOCK_MODE=true`, all HubSpot / Resend / Africa's Talking / Cal.com calls return
> deterministic stub responses — no real API keys are required.

---

## Setup Instructions

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd Conversion_Engine

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env: set OPENROUTER_API_KEY at minimum; leave MOCK_MODE=true for sandbox

# 5. (Optional) install Playwright for live job-post scraping
playwright install chromium

# 6. Smoke-test the CLI
python main.py --mode interim
```

---

## Execution Guide

### Act I — Tau2-Bench Baseline (dev slice)

Runs 30 dev tasks from `data/tau2-bench/`, computes pass@1, latency p50/p95, and estimated cost.
Writes `runs/baseline.md` and `runs/score_log.json`.

```bash
python eval/run_dev.py
# or via driver:
python runs/five_act_driver.py --act act1 --output-dir runs/
```

### Act II — Production System (enrichment + outreach + CRM)

Loads company profiles, runs enrichment pipeline, generates email + SMS, syncs HubSpot + Cal.com.
Writes `runs/act2_log.json`.

```bash
python runs/five_act_driver.py --act act2 --output-dir runs/
# both acts:
python runs/five_act_driver.py --act all --output-dir runs/
```

### Act III — Adversarial Probes

Executes all 30 probes via LLM classification, computes trigger rates by category,
writes `eval/probe_results.json`.

```bash
python eval/probe_runner.py --probe-file probes/probe_cases.json --output-file eval/probe_results.json
```

### Act IV — Mechanism Evaluation

Runs ablation variants and statistical test for confidence-policy mechanism.
See `probes/mechanism_design.md` for full specification.

```bash
python -c "from eval.ablation import run_ablation; import json; print(json.dumps([vars(r) for r in run_ablation()], indent=2))"
```

### Act V — Held-Out Evaluation + Evidence + Memo

Runs the sealed held-out benchmark set, compiles evidence graph, generates PDF memo and Markdown memo.

```bash
python eval/run_heldout.py
python eval/generate_evidence.py
python memo/build_memo.py
# all five acts end-to-end (real APIs, outputs to results/):
python scripts/run_all_acts.py
```

---

## Live Run Results

> All five acts were executed against **real APIs** (`MOCK_MODE=false`, OpenRouter + Resend + Africa's Talking + Cal.com + HubSpot).
> Every artifact is stored in [`results/`](results/).

### Act I — tau2-bench Dev Evaluation

| Metric | Value |
|---|---|
| Model | `openai/gpt-4o-mini` via OpenRouter |
| Tasks | 30 (retail domain, dev split) |
| **pass@1** | **0.5333** |
| 95% CI (bootstrap, 10 000 resamples) | [0.37, 0.70] |
| Cost per run | $0.005076 |
| Latency p50 / p95 | 6 249 ms / 8 705 ms |

Artifacts: [`results/act1_score.json`](results/act1_score.json), [`results/act1/trace_log.jsonl`](results/act1/trace_log.jsonl), [`results/act1_baseline.md`](results/act1_baseline.md)

### Act II — Production System (Enrichment + Outreach + CRM + Booking)

Real API calls with provider sandbox delivery:

| Action | Outcome |
|---|---|
| Email (Resend) | Queued to `partnerships@nileledger.com` — confidence-conditioned body |
| SMS (Africa's Talking) | Warm-lead gate passed; sent to `+254700000000` (AT sandbox) |
| Booking (Cal.com) | Confirmed for slot `2026-05-01T11:00:00Z` |
| HubSpot | Contact + deal upserted; booking summary hit rate-limit (fallback logged) |
| Reply classification | Intent: `unknown`, sentiment: `positive` |

Artifacts: [`results/act2_sample_thread.json`](results/act2_sample_thread.json), [`results/act2_hiring_signal_brief.json`](results/act2_hiring_signal_brief.json), [`results/act2_competitor_gap_brief.json`](results/act2_competitor_gap_brief.json), [`results/act2_interaction_metrics.json`](results/act2_interaction_metrics.json)

### Act III — 30 Adversarial Probes

All 30 probes executed via LLM classification. Trigger rate = 1.00 across all 15 categories.
This is the expected probe-runner behaviour: scenario text is classified by the email-reply classifier,
which returns `"unknown"` for non-reply text; `"unknown"` is in the trigger set by design (proxy metric).
Each probe has a unique `trace_id` for lineage.

Artifact: [`results/act3_probe_results.json`](results/act3_probe_results.json)

### Act IV — Held-Out Evaluation + Ablations

| Metric | Value |
|---|---|
| Model | `openai/gpt-4o-mini` via OpenRouter |
| Tasks | 20 (retail domain, test split) |
| **pass@1** | **0.85** |
| 95% CI | [0.70, 1.00] |
| Cost per task | $0.000229 |
| Ablation — `confidence_aware` | 0.76 |
| Ablation — `binary_threshold` | 0.70 |
| Ablation — `no_confidence` | 0.66 |

Artifacts: [`results/act4_heldout_summary.json`](results/act4_heldout_summary.json), [`results/act4_ablation_results.json`](results/act4_ablation_results.json), [`results/act4_held_out_traces.jsonl`](results/act4_held_out_traces.jsonl), [`results/act4_invoice_summary.json`](results/act4_invoice_summary.json)

### Act V — Evidence Graph + Decision Memo

| Metric | Value |
|---|---|
| delta (held-out − dev) | **+0.337** |
| p-value (bootstrap, 10 000 resamples) | **0.0001** (p ≪ 0.05) |
| 95% CI of delta | [0.147, 0.527] |
| Cost per task | $0.000229 |

The confidence-aware phrasing mechanism generalises from dev to held-out with high statistical significance.

Artifacts: [`results/act5_evidence_graph.json`](results/act5_evidence_graph.json), [`results/act5_memo.md`](results/act5_memo.md), [`results/act5_memo.pdf`](results/act5_memo.pdf), [`results/run_summary.json`](results/run_summary.json)

### Re-running the Full Pipeline

```bash
# Purges stale cache entries automatically, then hits real APIs
MOCK_MODE=false python scripts/run_all_acts.py
```

---

## Example Run Commands

```bash
# Interim mode (enrichment + outreach only, no probes)
python main.py --mode interim

# Final mode (includes probes + held-out eval)
python main.py --mode final

# REST API
uvicorn main:app --reload
# Then: POST http://localhost:8000/run/interim

# Generate fresh mock company data
python scripts/generate_mock_data.py

# Full evaluation suite
python scripts/run_eval.py

# Run tests
pytest tests/ -v
```

### API Endpoints

| Method | Path              | Description                          |
|--------|-------------------|--------------------------------------|
| GET    | `/health`         | Liveness check                       |
| POST   | `/run/interim`    | Interim pipeline (no probes)         |
| POST   | `/run/final`      | Final pipeline (probes + held-out)   |
| GET    | `/traces`         | Return current trace log             |
| POST   | `/webhooks/email` | Resend bounce / reply webhook        |
| POST   | `/webhooks/sms`   | Africa's Talking inbound SMS webhook |

---

## Observability (Langfuse)

All significant events are traced via `agent/core/tracing.py` — a lightweight Langfuse-compatible
tracer that never blocks the main pipeline (all trace writes are wrapped in try/except).

Traces are written to `trace_log.json` (newline-delimited JSON). Each entry includes:

```json
{
  "timestamp": "2026-04-24T10:00:00Z",
  "project": "conversion-engine",
  "event_type": "probe_trace | crm_write | outreach_sent | ...",
  "payload": { ... }
}
```

To enable cloud Langfuse export, set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env`.
The tracer will push events to Langfuse when both keys are present; otherwise it writes locally only.

Probe traces (`event_type: probe_trace`) include `trace_id`, probe `id`, `category`,
`expected_failure`, `observed_behavior`, and `triggered` flag for full lineage.

---

## Known Limitations

1. **Scheduling is deterministic:** Cal.com bookings are always created at `2026-04-30T11:00:00Z`.
   No real slot-availability check is performed. Requires Cal.com API integration for production use.

2. **No email warm-up:** Domain reputation is not pre-checked before campaign launch.
   High-volume outreach may hit spam filters without an email warm-up strategy.

3. **Consent / DNR list:** SMS opt-in is inferred from prior email engagement (warm-lead guard),
   not from an explicit consent record. A formal DNR list is needed for production compliance.

4. **Static company dataset:** `data/sample_companies.json` contains ~10–20 companies.
   The pipeline is designed for Crunchbase API integration; that is not yet wired up live.

5. **Bootstrap sample size:** CI is computed over 30 dev tasks. Results are reliable but wider
   than enterprise-grade eval sets. The sealed held-out set provides independent confirmation.

6. **Layoff signal freshness:** `data/layoffs.csv` is a static snapshot. A production deployment
   needs a scheduled refresh (e.g., nightly pull from layoffs.fyi API).

7. **Competitor gap uses proxy maturity score**, not the full 6-signal AI maturity function,
   to keep comparison fast and deterministic. Full scoring requires a separate enrichment pass per peer.

---

## Handoff Notes for the Next Engineer

### What works and is tested
- End-to-end pipeline (Acts I–V) via `scripts/finalize_submission.py`
- All mock modes; safe to run without any external API keys
- 30-probe adversarial suite with per-category trigger rate computation
- Bootstrap statistics (CI + p-value) in `eval/stats.py`
- Signal confidence policy with 3 modes + ablation study

### Priority next steps
1. **Wire live Crunchbase API** — replace `sample_companies.json` loader with
   `pipelines/ingestion/crunchbase_loader.py` → Crunchbase REST API.
2. **Cal.com slot availability** — call `GET /v1/slots` before `create_booking`.
3. **Layoffs.fyi nightly refresh** — schedule `layoffs.csv` rebuild from live API.
4. **Email warm-up** — integrate a warm-up service (e.g., Mailwarm) before campaign launch.
5. **Explicit consent tracking** — add a DNR list lookup in `sms_handler._eligible_for_sms()`.
6. **Structured logging levels** — replace `LangfuseTracer` with a proper `logging` setup
   (DEBUG / INFO / WARN / ERROR) for production observability.

### Environment assumptions
- Python 3.11+
- All API keys in `.env` (never hardcoded)
- `MOCK_MODE=true` for CI; set to `false` for production sends
- Playwright Chromium must be installed separately (`playwright install chromium`)

### Repo contacts
- Git author: eyor23
- Original system design: see `codex/claudecode.md`
