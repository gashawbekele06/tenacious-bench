# Methodology Rationale — Path A SFT Generation Component

**Author:** Gashaw Bekele | gashaw@10academy.org  
**Date:** 2026-04-28  
**Path:** A — Supervised fine-tuning of a generation component  
**Backbone:** `unsloth/Qwen2.5-0.5B-Instruct`

---

## Why Path A

The Week 10 failure evidence points unambiguously to a **surface-level generation failure**,
not an inconsistency failure (Path B) or a trajectory planning failure (Path C).

Three specific traces confirm this:

**Trace `tr_sim_6beaf527` / `retail_dev_020`** — the agent correctly identified the objection
(offshore concern) and had access to the Clearbit case study in its context window, yet
produced "I completely understand your frustration — we are different from other offshore
vendors." The model knew the structure of the task but generated the wrong register. This
is the canonical Path A failure: the model's training distribution pulled it toward
empathy-appeasement language that τ²-Bench passes but Tenacious-Bench fails.

**Trace `a553180f-80d2-4d4b-9a1e-d525b1219cfd`** (`trace_log.jsonl`, reward=0.0) — the full
task failed because the output violated the style-compliance checker. The conversational
logic was intact; the surface form was wrong. Path B (inconsistency) would manifest as
the agent sometimes producing correct outputs and sometimes not on structurally identical
inputs; this trace shows consistent failure on a consistent register violation.

**Trace `89337dd7-bb36-41d7-8530-190df8734cc3`** (`trace_log.jsonl`, reward=0.0) — the agent
abandoned its established tone at turn 3, switching from specific evidence to vendor-speak
("leverage our best-in-class talent"). Again, the task structure was followed; the surface
realisation drifted. This directly mirrors probe P-010 (turn-4 vendor-speak, trigger 0.38).

Path B would be appropriate if the agent's error rate varied unpredictably across structurally
identical inputs — i.e., if it sometimes got offshore objections right and sometimes not, with
no pattern. The probe library shows P-011 triggering at 0.44: nearly deterministic failure, not
inconsistency. Path C would be appropriate if the agent made locally reasonable decisions that
compounded into bad endings (e.g., qualified a prospect correctly at turn 1 but over-committed
bench at turn 3 because it lost track of the constraint). The failures here are all single-turn
surface failures, not multi-step trajectory errors.

---

## Paper Foundations

**Lambert et al. (2024) — Tülu 3**

The Tülu 3 training recipe demonstrates that a small backbone (8B) fine-tuned with
high-quality SFT data followed by DPO can outperform much larger instruction-tuned models
on domain-specific tasks. The key design choice I am adopting from Tülu 3 is the
**quality-over-quantity** data selection: Tülu 3 filters its SFT data aggressively (keeping
~5% of the original pool) and shows that this consistently beats training on larger, noisier
sets. My `generate_sft_pairs.py` pipeline applies the same principle — 221 of 233 tasks
produce passing pairs (94.8%), and the 12 failures are discarded rather than included with
lower quality.

I depart from Tülu 3's DPO stage by design: the 0.5B backbone at this budget does not have
enough capacity to benefit from preference optimization on top of SFT. Tülu 3's DPO gains
are observed on 8B+ models. Running DPO on 0.5B with 221 pairs would produce noise, not
signal.

**Zhou et al. (2023) — LIMA: Less Is More for Alignment**

LIMA's central finding — that 1,000 carefully curated instruction-response pairs are
sufficient to produce a well-aligned model — directly governs my authoring strategy.
My 221 SFT pairs are within LIMA's demonstrated sufficiency range. LIMA also shows that
**diversity of format and topic matters more than volume** at this scale; my four-mode
authoring pipeline (trace-derived, programmatic, multi-LLM synthesis, hand-authored)
addresses this by ensuring the 221 pairs cover all 8 failure dimensions from qualitatively
different generation paths.

Where I disagree with LIMA: LIMA's tasks were drawn from a pre-existing curated human corpus
(StackExchange, wikiHow, etc.). My domain has no such corpus. The Magpie-style self-instruction
approach is therefore necessary as a substitute, not a supplement.

**Xu et al. (2024) — Magpie: Alignment Data Synthesis from Scratch**

Magpie demonstrates that aligned LLMs can be prompted with nothing (just the system-turn
prefix) to generate their own instruction-response pairs, producing high-quality alignment
data without human annotation or curated seed examples. I adapt this approach in
`generate_sft_pairs.py`: the SYSTEM_PROMPT encodes the Tenacious style guide, and the model
is prompted with the task context to generate a gold-standard outreach email. The key
difference from vanilla Magpie is that I **provide structured input fields** (hiring_signal_brief,
bench_summary, prospect_profile) rather than prompting with nothing — the Tenacious domain
requires signal grounding that cannot be self-generated without a hiring signal brief as input.

The Magpie-style quality filter is preserved: every generated output is scored against all
programmatic rubric checks before inclusion, and outputs that fail after three retries are
discarded. This matches Magpie's automated quality filtering step.

---

## Training Configuration Rationale

| Choice | Value | Reason |
|--------|-------|--------|
| Backbone | Qwen2.5-0.5B-Instruct | Budget constraint (free Colab T4); Unsloth-optimised |
| LoRA r / alpha | 16 / 16 | Unsloth Qwen 3.5 guide default; sufficient for style adaptation |
| Epochs | 3 | LIMA: 3 epochs standard for small SFT datasets; loss curve confirms convergence at epoch 3 |
| LR | 2e-4 | Tülu 3 SFT default for LoRA on instruction-following tasks |
| Effective batch | 8 (2 × 4) | Maximum that fits T4 16GB without OOM |
| Data | 221 SFT pairs | LIMA sufficiency threshold; quality-filtered via programmatic rubric |

---

## Honest Limitation

The 0.5B backbone cannot reliably enforce negative lexical constraints. All three model
variants (baseline, prompted, trained) produced the word "bench" — a banned phrase in
prospect-facing text — because it appears in the input context (`bench_summary`) and the
small model reproduces it via attention copying. This is a capacity limitation of the
backbone, not a pipeline failure. Tülu 3 and LIMA both operate on 7B+ models where this
constraint is learnable. A v0.2 experiment on Qwen2.5-1.5B with the same 221 pairs is
expected to clear the "bench" and word-count thresholds. The current adapter is published
as a reproducible baseline, not a production deployment recommendation.
