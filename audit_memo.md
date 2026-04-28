# Audit Memo — Tenacious-Bench v0.1

**Author:** Gashaw Bekele  
**Email:** gashaw@10academy.org  
**Date:** 2026-04-28  
**Word count:** ~580  

---

## The Gap

τ²-Bench retail evaluates binary task completion: did the agent send the email,
look up the company, book the slot? It rewards any coherent output that clears
the tool-call graph. It does not measure whether the email sounds like Tenacious
wrote it, whether the outreach is grounded in the specific hiring signal, or
whether the agent correctly represents bench capacity. A Week 10 agent that
triggers the offshore-perception objection 44% of the time (P-011) scores 0.73
pass_at_1 on τ²-Bench retail because those two things are unrelated. That is
the gap this benchmark is designed to close.

---

## Evidence From Week 10

| Trace / Task ID | What Failed | Why τ²-Bench Passes It |
|-----------------|-------------|------------------------|
| `tr_sim_6beaf527` / `retail_dev_015` (cross_sell_decline) | Agent failed to handle a soft product decline, defaulting to generic upsell language rather than acknowledging the stated reason | τ²-Bench grades tool invocation — email was sent, task counts as attempted |
| `tr_sim_6beaf527` / `retail_dev_020` (escalation_decline) | Agent used defensive appeasement ("I completely understand your frustration") instead of specific evidence — mirroring P-011 signature | τ²-Bench scores pass/fail on intent completion, not tone register |
| `tr_sim_6beaf527` / `retail_dev_013` (partial_refund) | Agent confirmed a partial resolution without verifying constraints, analogous to P-007/P-009 bench over-commitment | τ²-Bench doesn't check whether the committed action is operationally feasible |
| `a553180f-80d2-4d4b-9a1e-d525b1219cfd` (trace_log.jsonl, reward=0.0) | Full task failure — agent output was semantically correct but violated register constraints | Reward=0 here is incidental; τ²-Bench cannot distinguish a register violation from a structural one |
| `89337dd7-bb36-41d7-8530-190df8734cc3` (trace_log.jsonl, reward=0.0) | Agent abandoned the established conversational tone at turn 3, switching from specific evidence to vendor-speak | τ²-Bench has no per-turn tone check |

**Probe IDs from Week 10 probe library mapping to these failures:**

- **P-010** (trigger 0.38): Turn-4 email drifts to "leverage our best-in-class offshore talent" — banned by style guide. τ²-Bench would mark the email as sent and score pass.
- **P-011** (trigger 0.44 — highest in library): Offshore-perception objection elicits generic defensive reply rather than specific Tenacious case-study evidence. τ²-Bench does not score the reply content.
- **P-012** (trigger 0.17): Agent asserts funding fact with confidence < 0.55 — τ²-Bench has no confidence-gate check.
- **P-004** (trigger 0.22): Velocity claim ("hiring tripled") made on a point-estimate signal (delta_60d=0). Generic benchmarks have no signal-veracity dimension.
- **P-007** (trigger 0.31): Agent commits to 6 ML engineers when bench shows only 3 available. τ²-Bench does not read bench_summary.json.
- **P-019** (trigger 0.23): Cal.com booking confirmed with no delivery manager available. τ²-Bench grades "booking action taken" not "booking was operationally valid".
- **P-028** (trigger 0.40): Sector-wide trend claimed from peer_count=2. No public benchmark checks statistical sufficiency of competitive claims.
- **P-030** (trigger 0.24): Specific tool ("running vLLM in production") cited from a job-description keyword, not a confirmed deployment. τ²-Bench cannot distinguish evidence quality.

---

## What Tenacious-Bench Must Measure (Path A Focus)

Because the dominant failure is **surface-level tone drift**, not structural task failure,
the benchmark must enforce machine-verifiable style constraints:

1. **Tone-preservation** — zero banned phrases from the 23-phrase style guide AND average ≥ 4/5 across 5 tone markers (direct, evidence-based, specific, low-pressure, competence-signaling).
2. **Signal-grounding** — at least one phrase from `required_signal_references` appears verbatim; confidence-gated claims use hedged language when `signal_confidence < 0.55`.
3. **Bench-commitment accuracy** — no headcount or start-date commitment that exceeds `bench_summary` constraints; verifiable by regex against committed figures.
4. **Prospect-qualification** — segment assignment and disqualifier logic enforced before outreach framing; checkable via prospect_profile fields.
5. **Discovery-call booking** — output contains a valid calendar link pattern (cal.com / calendly / savvycal) and clear CTA.
6. **Objection-handling** — multi-turn tasks: reply references specific evidence (case study name or outcome metric), not generic reassurance.
7. **Multi-turn coherence** — tone markers hold across turns 1–4; no drift to banned phrases in later context.
8. **Cost-accuracy** — bench commitments do not exceed available capacity; start dates respect deploy windows.

---

## Why Existing Benchmarks Fall Short

τ²-Bench (Yao et al., 2024) scores a retail agent on whether tool calls complete
and whether the end-state matches a reference. AgentBench (Liu et al., 2023)
tests operating-system and web tasks. Neither encodes a domain-specific style
guide, a real capacity constraint file, or a confidence-gated claim policy.
They are correct to omit these — they are general benchmarks. But Tenacious
operates in a narrow domain where the brand voice is the product: a CTO who
receives generic offshore-vendor language disengages before reading the signal.
The Week 10 probe library proved this with a 0.44 trigger rate on P-011 — nearly
one in two runs produced a style-guide violation that a general benchmark would
have marked as a pass.

---

## Conclusion

Tenacious-Bench is needed because the relevant failure mode (tone drift under
objection pressure) is invisible to task-completion metrics. The benchmark closes
this gap by encoding the Tenacious style guide as machine-checkable rubric
dimensions, grounding every task in real hiring-signal data structures, and
requiring that LLM judge scores hold on all five tone markers. The Path A
training data this benchmark generates will directly address P-010 and P-011
by providing (input, Tenacious-style output) pairs that teach tone maintenance
across long context windows.
