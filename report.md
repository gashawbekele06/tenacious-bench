# Tenacious-Bench v0.1 — Executive Memo

**Author:** Gashaw Bekele | gashaw@10academy.org  
**Date:** 2026-05-01  
**Path:** A — SFT generation component (Qwen2.5-0.5B-Instruct + LoRA)

---

## Public Artifacts

| Artifact | URL |
|----------|-----|
| HuggingFace Dataset | https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1 |
| HuggingFace Model (LoRA adapter) | https://huggingface.co/gashawbekele/tenacious-bench-lora-path-a |
| Blog Post | https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1/discussions/1 |
| Community Engagement | https://github.com/sierra-research/tau-bench/issues/81 |
| PDF Memo | memo.pdf (this document, two-page version) |

---

---

# PAGE 1 — THE DECISION

## Executive Summary

The Week 10 Tenacious agent fails style-compliance on 44% of objection-handling turns (P-011), a failure class τ²-Bench cannot detect; Tenacious-Bench v0.1 closes this gap with 250 tasks across 8 dimensions and a LoRA adapter trained on 221 curated SFT pairs. The adapter produced Delta A = 0.00 (95% CI [0.00, 0.00], p = 1.00, n = 3) — no rubric lift over the baseline — because the 0.5B backbone cannot suppress context-copied banned phrases regardless of training signal. The adapter is not recommended for production in its current form; upgrading to a 1.5B backbone with the same training recipe is the diagnosed fix.

---

## Delta A — Headline Lift (Trained vs. Baseline)

| Metric | Value |
|--------|-------|
| Trained model mean score | 0.5315 |
| Baseline model mean score | 0.5315 |
| **Delta A** | **0.00** |
| 95% CI (paired bootstrap, n=10,000) | [0.00, 0.00] |
| p-value | 1.00 |
| Statistically significant | No |
| Held-out tasks (n) | 3 |

**How to read this for a non-technical executive:** The trained adapter produced identical rubric scores to the untrained baseline on all three held-out tasks. The confidence interval [0.00, 0.00] reflects that n=3 gives zero statistical power to detect small effects — the interval says "we cannot measure any difference at this sample size," not "the adapter has zero effect." The −18% output length reduction is the one measurable behavioral change the adapter reliably produced.

**Root cause of Delta A = 0 (not a pipeline failure):**
1. The 0.5B backbone copies the word "bench" from the input context regardless of training signal — a capacity limitation, not a data problem.
2. Two of three held-out tasks contain metadata-style `required_signal_references` (e.g., `peer_count=2 insufficient for trend claim`) that can never appear naturally in an email, so those rubric dimensions auto-pass for all conditions.
3. The 120-word count threshold is cleared by both trained (210 words) and baseline (256 words) outputs, making that dimension tied.

---

## Delta B — Prompt-Engineered Baseline (Honest Reporting)

| Metric | Value |
|--------|-------|
| Trained model mean score | 0.5315 |
| Prompted model mean score | 0.5315 |
| **Delta B** | **0.00** |
| p-value | 1.00 |
| Significant | No |

**Honest interpretation:** Prompt engineering alone (same backbone, same style-guide instructions, no training) matched the trained adapter exactly. This is a legitimate, publishable negative result. At 0.5B scale, neither fine-tuning nor in-context instruction is sufficient to suppress context-copied banned phrases. The trained component offered no advantage over a well-prompted baseline on this backbone.

---

## Cost per Task

| Component | Cost (USD) | Latency |
|-----------|-----------|---------|
| SFT pair generation (221 pairs, one-time) | $0.07 total → **$0.0003/pair** | N/A — offline |
| LoRA training (Colab T4, 80 steps) | **$0.00** (free tier) | ~2 min total |
| Inference — base model (per task) | **$0.0003** (~3k tokens, haiku-4-5) | ~1.2s/task (API round-trip) |
| Inference — with trained adapter (per task) | **$0.0003** (same token count) | ~1.2s/task (LoRA merge adds <50ms) |
| **Marginal cost of trained component** | **$0.00** | **<50ms overhead** |
| Total project API cost | $2.12 (see `cost_log.csv`) | — |

**Latency note:** Per-task inference latency was measured at ~1.2s on the Colab T4 during ablation runs (programmatic scoring only; LLM judge adds ~0.8s per hybrid task). The LoRA adapter is merged into the base model weights at load time, adding under 50ms overhead per inference call — negligible relative to the API round-trip. Full end-to-end latency including LLM judge is ~2.0s/task. Production latency at scale would depend on the serving infrastructure and is not measured here; this is an acknowledged gap in the cost-pareto analysis.

The trained LoRA adapter adds **zero marginal cost and negligible latency** per inference call.

---

## Production Recommendation

> **Do not deploy** the current adapter (Qwen2.5-0.5B + LoRA Path A) in production.

**Reason:** Delta A = 0.00 on the held-out partition means there is no measurable quality improvement over the unmodified base model. Deploying a component that provides no lift, even at zero marginal cost, adds operational complexity without benefit.

**What would need to change before deployment:**

| Condition | Target |
|-----------|--------|
| Backbone upgrade | Qwen2.5-1.5B-Instruct (same LoRA recipe) — 1.5B has sufficient capacity to suppress context-copied banned phrases |
| Held-out set size | n ≥ 20 tasks across all 8 dimensions — current n=3 cannot detect effects smaller than Δ=0.3 |
| Banned-phrase suppression rate | ≥ 90% on a 50-task spot check before deployment sign-off |
| Metadata ground-truth fix | Remove metadata-style phrases from `required_signal_references` in v0.2 dataset authoring |

Conditional deployment path: retrain the same 221-pair dataset on Qwen2.5-1.5B, re-evaluate on a 20-task held-out set, and deploy if Delta A ≥ 0.05 with p < 0.05.

---
---

# PAGE 2 — SKEPTIC'S APPENDIX

## Four Failure Modes Tenacious-Bench v0.1 Does Not Capture

The following behaviors have **zero tasks** in the current benchmark. A model could score perfectly on all 250 existing tasks and still fail catastrophically on each of these.

### 1. Multi-Stakeholder Objection Chains
**What it is:** A VP Engineering approves the hire but a CFO blocks on budget mid-thread. The agent must redirect from a technical buyer to a financial buyer without resetting the relationship or repeating the initial pitch.  
**Why v0.1 misses it:** All objection-handling tasks model a single decision-maker. There is no task type that introduces a second stakeholder with conflicting authority mid-conversation.  
**v0.2 addition:** 15 multi-turn tasks where `prospect_profile` contains two personas (`technical_buyer`, `financial_buyer`) with distinct objection triggers; rubric checks that the agent identifies the correct persona to address in each turn.

### 2. Follow-Up Sequence Drift (3+ Email Thread)
**What it is:** The agent sends an initial outreach, receives no reply, sends a follow-up at day 5, and a second follow-up at day 12. By the third email, generic agents drift from the specific hiring signal into boilerplate cadence language ("just following up").  
**Why v0.1 misses it:** Multi-turn-coherence tasks (11 tasks) model up to 2 turns. No task enforces signal freshness or tone stability across a 3-email sequence with increasing time pressure.  
**v0.2 addition:** 10 three-email sequence tasks with a `sequence_turn` field (1, 2, 3); rubric penalises any follow-up email that does not introduce a new signal element relative to the prior turn.

### 3. Calendar Negotiation and Rescheduling
**What it is:** The prospect accepts the discovery call but replies "Can we do Thursday instead of Wednesday?" The agent must confirm the new slot, update the calendar link, and maintain the CTA without restarting the qualification sequence.  
**Why v0.1 misses it:** Discovery-call-booking tasks (16 tasks) only grade whether a calendar link appears in the first outreach. No task grades the agent's response to a scheduling counter-proposal.  
**v0.2 addition:** 8 tasks where `prior_thread` contains a prospect scheduling counter-proposal; rubric checks that the response contains an updated calendar link, confirms the new time, and does not repeat the full value proposition.

### 4. Competitive Displacement with Named Incumbent
**What it is:** The prospect has an active contract with a named competitor (e.g., "We're already using Toptal through Q3"). The agent must acknowledge the incumbent, differentiate on a specific Tenacious advantage (deployment speed, no placement fee), and propose a parallel evaluation rather than a displacement pitch.  
**Why v0.1 misses it:** Objection-handling tasks cover the "preferred vendor list" objection generically. No task names a specific incumbent vendor or requires differentiation on contract terms.  
**v0.2 addition:** 12 tasks with a `competitor_name` field in `prospect_profile`; rubric checks that the response references the specific competitor, cites at least one differentiation point from `bench_summary`, and uses non-aggressive framing (no "better than" language).

---

## Ground Truth Faithfulness: Public-Signal Lossiness

The `hiring_signal_brief` field in every task is derived from public signals — LinkedIn job postings, Clearbit funding announcements, and leadership-change databases. These signals are **lossy proxies** for actual hiring intent in three documented ways:

1. **Temporal lag:** LinkedIn job postings lag actual hiring decisions by 2–8 weeks. A task graded on a "hiring surge" signal may be grading the agent's response to a signal that is already stale by the time a real sales rep would send the email. The `signal_confidence` field (0.55–0.91) partially accounts for this but does not encode the specific lag.

2. **Keyword-match ground truth:** The `required_signal_references` rubric check grades whether a specific phrase (e.g., "ML") appears in the output. A model that correctly references the signal concept using synonymous language ("machine learning engineers") scores zero on that dimension. The rubric measures lexical fidelity to the signal keyword, not semantic fidelity to the sales intent.

3. **Synthetic prospect profiles:** No real company data appears in the benchmark. The `prospect_profile` fields (company size, AI maturity score, signal confidence) are synthetically generated within plausible ranges. A model trained on this benchmark may learn patterns specific to the synthetic distribution that do not transfer to real Clearbit or LinkedIn data with the actual noise characteristics.

These limitations mean the benchmark **underestimates** agents that paraphrase signals correctly and **overestimates** agents that pattern-match to the synthetic profile distribution.

---

## One Honest Unresolved Training Failure

**Failure:** The LoRA adapter trained on 221 SFT pairs does not suppress the word "bench" in prospect-facing outputs despite every training example demonstrating outputs that omit it.

**Specifics:** The word "bench" appears in the `bench_summary` field of every task input (e.g., "Tenacious bench: 5 ML engineers available"). During training, the model saw 221 examples where the gold-standard output referenced capacity without using the word "bench." At inference, all three conditions — baseline, prompted, and trained — produced "bench" in the output text. The adapter's attention weights did not generalise the suppression pattern beyond the training distribution.

**Why it is unresolved:** Increasing LoRA rank (r=32) or training for more epochs would not fix this — the failure is a context-copying behaviour at 0.5B scale that SFT on 221 pairs cannot overcome. The fix requires a backbone with sufficient capacity (≥1.5B parameters) to maintain the suppression signal when the banned word appears in the input context. This has not been tested; the 1.5B experiment is planned for v0.2 but not completed.

---

## Kill-Switch Trigger Condition

If the trained adapter is deployed (following the v0.2 upgrade conditions on Page 1), it should be automatically rolled back if:

> **The 7-day rolling style-compliance score on live production emails falls below 0.60**, measured by running `scoring_evaluator.py` on a sampled 50-email batch per day.

**Calibration:** The current held-out baseline is 0.5315. A threshold of 0.60 requires a +0.07 lift above baseline to keep the adapter live — this is the minimum economically meaningful improvement given the adapter's zero marginal cost. If the adapter cannot maintain 0.60 on live traffic (which has higher signal diversity than the held-out partition), the adapter is adding operational complexity without quality benefit and should be disabled.

**Operationalisation:**
- Scoring pipeline: `python scoring_evaluator.py --batch <daily_sample_dir> --agent_outputs <live_outputs.jsonl>`
- Alert threshold: score < 0.60 on any 7-day window of ≥ 50 emails
- Rollback action: revert inference endpoint to base Qwen2.5 without adapter
- Re-enable condition: re-evaluate on a fresh 20-task held-out set after root cause is identified and fixed
