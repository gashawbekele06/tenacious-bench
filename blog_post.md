# Building Tenacious-Bench: What Happens When You Try to Evaluate an AI Sales Agent on Something That Actually Matters

*by Gashaw Bekele — 2026-04-29*

---

Most AI benchmarks are designed to be solvable. The questions have ground-truth answers,
the scoring is deterministic, and the leaderboard rewards the model that gets the most
right. That's fine for coding or math. It's not fine for evaluating a B2B sales agent
whose job is to write outreach emails that a real person will either respond to or
delete.

This post is about building Tenacious-Bench v0.1: a 250-task evaluation benchmark for
a sales development agent, and what I learned when the fine-tuned model scored exactly
as well as the untrained baseline.

---

## The Problem with τ²-Bench

The Week 10 baseline agent scored 0.61 on τ²-Bench, an existing agentic evaluation
framework. τ²-Bench measures whether the agent completed the task — did it produce an
email, did it include the right prospect name, did it respond to the objection?

What τ²-Bench doesn't measure is *how* the agent completed the task. The agent could
score perfectly on τ²-Bench while producing emails that no prospect would ever respond to:
emails that open with "I completely understand your frustration," that end with
"leverage our best-in-class talent," that refer to the agent's own employer as "the
bench" in a document addressed to a skeptical VP.

The probe library confirmed this. P-010 found a 0.38 trigger rate for vendor-speak
at turn 4. P-011 found a 0.44 trigger rate for offshore-appeasement language. These
aren't occasional slips — they're near-deterministic failures on a specific register.

Tenacious-Bench exists to measure those failures.

---

## What Tenacious-Bench Actually Measures

The benchmark has 250 tasks across 8 dimensions:

- **Tone preservation** — does the output maintain Direct/Grounded/Honest/Professional/
  Non-condescending register across the full response?
- **Signal grounding** — does the email reference a specific, verifiable hiring signal
  (a role posting, a funding announcement) with a numeric anchor?
- **Objection handling** — does the agent respond to skepticism (offshore concern,
  pricing concern) with evidence, not empathy-appeasement?
- **Bench exposure avoidance** — does the agent avoid revealing internal staffing
  terminology in prospect-facing text?
- **Calendar conversion** — does the email include a concrete scheduling action
  (a calendar link or a specific day/time proposal)?
- **Competitive displacement** — does the agent make a specific differentiation claim
  rather than a generic one?
- **Multi-stakeholder alignment** — does the email address both the technical and
  business decision-maker's concerns?
- **Upsell sequencing** — does the agent sequence the conversation correctly (qualify
  first, expand later)?

Each task has a rubric with 3–5 checks. Four check types: `not_contains` (banned
phrases), `contains` (required evidence), `regex` (calendar links, phone numbers),
and `word_count`. For style-heavy dimensions, a fifth check — `llm_score` — asks
a judge model to score the output against a five-marker tone rubric on a 1–5 scale.
A hybrid score combines programmatic checks (weighted) with the LLM score.

---

## Why I Chose Path A (SFT)

Three specific failure traces from Week 10 made the diagnosis clear.

**Trace `tr_sim_6beaf527`:** The agent correctly identified the objection (offshore
concern) and had access to the Clearbit case study in its context window. It produced
"I completely understand your frustration — we are different from other offshore vendors."
The model *knew* the structure of the task. It generated the wrong register. This is
a surface-level generation failure, not a knowledge failure.

**Trace `a553180f`:** Full task failed because the output violated the style-compliance
checker. Conversational logic intact. Surface form wrong.

**Trace `89337dd7`:** The agent abandoned its established tone at turn 3, switching
from specific evidence to vendor-speak ("leverage our best-in-class talent"). Task
structure followed. Surface realization drifted.

Path B (preference optimization for consistency) would be appropriate if the agent's
error rate varied unpredictably on structurally identical inputs. The probe library
shows P-011 triggering at 0.44 — nearly deterministic failure, not inconsistency.

Path C (trajectory planning) would be appropriate if the agent made locally reasonable
decisions that compounded into bad endings. These are all single-turn surface failures.

Path A: supervised fine-tuning of the generation component.

---

## The Dataset: 250 Tasks, 4 Authoring Modes

Building a benchmark for this domain is harder than it looks. There is no StackExchange
for B2B outreach emails. There is no pre-existing corpus I can filter.

I used four authoring modes:

**Trace-derived (28.4%):** Real failure traces from Week 10, anonymized and converted
into evaluation tasks. These are the most diagnostically valid tasks — they correspond
to failures the agent actually produced.

**Programmatic (28.0%):** Tasks generated by template with parameter variation (prospect
industry, signal type, objection type). These provide systematic coverage of the failure
dimensions.

**Multi-LLM synthesis (39.6%):** Tasks generated by Qwen3-8B (via OpenRouter), then
filtered by a Claude judge. The judge rotation policy — Claude-generated tasks judged
by Qwen, Qwen-generated tasks judged by Claude — prevents preference leakage.

**Hand-authored (4.0%):** 10 high-difficulty adversarial tasks written manually to
probe edge cases the other modes wouldn't generate naturally.

Every task passed a three-check quality gate before inclusion. 12 of 233 training tasks
were discarded after failing three generation retries. The dataset was checked for
contamination: zero held-out tasks have 8-gram overlap or cosine similarity ≥ 0.90
with the training partition.

---

## The Fine-Tuning: What Worked and What Didn't

**Setup:** `unsloth/Qwen2.5-0.5B-Instruct`, LoRA r=16/alpha=16, 3 epochs, 2e-4 LR,
effective batch size 8, free Colab T4 GPU. Training time: ~2 minutes.

**What worked:** The loss curve dropped from 3.08 (step 10) to 0.42 (step 80) —
clear convergence. Trained outputs averaged 210 words vs baseline 256 words, an 18%
reduction. The adapter learned concision. The Qwen chat-template format was preserved
throughout.

**What didn't work:** Delta A = 0.0. Trained model score: 0.5315. Baseline score:
0.5315. p=1.0. Not significant.

Three root causes:

1. **Backbone capacity.** The 0.5B model cannot reliably enforce negative lexical
   constraints. "Bench" appears in the input context (`bench_summary`) and is
   reproduced via attention copying in all three conditions — baseline, prompted, and
   trained. This is a capacity limitation documented in the LIMA and Tülu 3 literature:
   those SFT gains are observed on 7B+ models.

2. **Metadata auto-pass.** Two of three held-out tasks have rubric check values that
   pass regardless of output content (a design artefact from the `_is_metadata_phrase()`
   guard that filters rubric annotations from natural text). Both conditions score
   identically on those tasks.

3. **Discriminating thresholds.** The 120-word count threshold: trained outputs
   (210w) and baseline outputs (256w) both clear it. The check doesn't discriminate.

---

## What This Means

Delta A = 0.0 is not a null result. It is a diagnosis.

The measurement failed before the model could. The held-out set (n=3) has insufficient
statistical power to detect a small effect. The rubric check values need to be set at
levels that actually discriminate between good and bad outputs, not levels that are
always passed.

The next version (v0.2) addresses these directly:
- Backbone: Qwen2.5-1.5B (same 221 SFT pairs)
- Held-out set: n≥20 with explicit audit to remove metadata auto-pass tasks
- Discriminating thresholds: word count ceiling at 250, not floor at 120

The 18% length reduction is a real signal. The adapter learned something. The
evaluation just couldn't measure it.

---

## Reproducibility

All artifacts are public:

- **Dataset:** [gashawbekele/tenacious-bench-v0.1](https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1)
- **Adapter:** [gashawbekele/tenacious-bench-lora-path-a](https://huggingface.co/gashawbekele/tenacious-bench-lora-path-a)
- **Code:** [github.com/gashawbekele06/tenacious-bench](https://github.com/gashawbekele06/tenacious-bench)
- **Scorer demo:** `python scoring_evaluator.py --demo`

Total cost to reproduce: ~$2.12 in API calls + free Colab compute.

---

## One Thing I'd Do Differently

I'd enforce partition quotas before generating tasks, not after.

The v0.1 actual split is 233/14/3 (train/dev/held-out) against a 50/30/20 target.
The held-out set ended up at 1.2% of the total because tasks were generated into
`train/` by default and partitioned retroactively. The statistical result is directly
affected by this: a 3-task held-out set can't detect anything.

The lesson: **set the held-out aside first, then generate training data.** Contamination
prevention should be enforced at generation time, not as a post-hoc check.

---

*Gashaw Bekele is a machine learning engineer at 10 Academy. This work was completed as
part of TRP1 Week 11.*
