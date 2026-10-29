# Booking Agent

An AI agent that books appointments for a solo service business over chat. It
checks real calendar availability, books the slot, answers questions about
services and pricing from a knowledge base (RAG), and hands off to a human —
with an explicit AI disclosure — when a request is outside booking.

> Built from a system I deployed for a real client (a solo nail studio). This
> repo uses a **synthetic "Polish & Co" stand-in** with fake calendar and
> pricing data; no real customer information is included.

<!-- TODO (Jack): once it's live, add a one-line link to the portfolio site. -->

## Why this exists

The production version runs on a no-code stack (n8n + Claude + Calendly) and is
live with a paying client. This repo re-implements the **core agent loop in
Python** to show the tool-calling, retrieval, and evaluation directly instead
of hiding them behind a visual workflow.

## Architecture

```
customer message
      │
      ▼
  Agent loop  ──► model picks a tool ──►  check_availability  ─► calendar
  (agent/core.py)                          book_appointment    ─► calendar
      ▲                                     get_service_info    ─► RAG (knowledge/)
      │                                     escalate_to_human   ─► human handoff + AI disclosure
      └──────────── tool result ◄───────────┘
      │
      ▼
  reply to customer
```

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env         # add your ANTHROPIC_API_KEY and MODEL
python -m agent "Can I book a gel manicure the week of June 15 2027?"
```

Interactive: `python -m agent`

## Evaluate it

```bash
python -m evals.run --selftest   # deterministic tool checks, no API key needed
python -m evals.run              # full agent eval vs the model (needs API key)
```

The full run reports a pass rate per category (booking, pricing, handoff, …).

<!-- TODO (Jack): paste the latest pass rate here once you've run it. -->

## Results (fill in from Phase 1 — these are the real-client numbers)

<!-- TODO (Jack): replace the placeholders below with the real metrics you pull
     from the live agent's logs. This table is what makes it a case study. -->

| Metric | Before | After |
|---|---|---|
| Booking conversion rate | _measuring_ | _measuring_ |
| Median response time | _measuring_ | _measuring_ |
| Human-handoff rate | _measuring_ | _measuring_ |
| Eval pass rate | — | _run evals_ |

**Diagnosis:** _one sentence on where the live agent was underperforming and what you changed._

## What I'd do next

<!-- TODO (Jack): honest limitations. E.g. swap the keyword retriever for real
     embeddings; wire check_availability to the live Google Calendar API;
     add rescheduling; expand eval coverage. -->

## Project layout

```
agent/        agent loop, tools, prompt, retriever, config
knowledge/    services, pricing, hours, policies, FAQ (synthetic)
data/         synthetic calendar + example conversations
evals/        test cases + runner
```
