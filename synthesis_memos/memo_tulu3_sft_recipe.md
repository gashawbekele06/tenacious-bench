# Synthesis Memo — Lambert et al. (2024): Tülu 3

**Author:** Gashaw Bekele  
**Date:** 2026-04-29  
**Paper:** Lambert et al. (2024). "Tülu 3: Pushing Frontiers in Open Language Model Post-Training."  
**Relevance:** Path A SFT data quality strategy and LoRA training configuration  

---

## Core Claim

Tülu 3 demonstrates that a small backbone (8B parameters) can outperform larger
instruction-tuned models on domain-specific tasks when fine-tuned with high-quality,
selectively filtered SFT data followed by DPO/RLVR. The recipe's central contribution
is the **quality-over-quantity** principle: Tülu 3 retains ~5% of its source data pool
after aggressive filtering, and this smaller high-quality set consistently beats training
on larger, noisier alternatives.

---

## Design Choices I Adopted

**1. Quality-over-quantity data filtering**

Tülu 3 applies a multi-stage filtering pipeline: deduplication, length filtering, quality
scoring, and task-specific validation before any pair enters training. I implement the same
principle in `generate_sft_pairs.py`: every generated output is scored against the full
programmatic rubric before inclusion; outputs failing after three retries are discarded
entirely. This produced 221 passing pairs from 233 tasks (94.8% pass rate) — a higher
retention rate than Tülu 3's ~5%, which reflects that my domain is narrower (single task
type) and my quality bar is domain-specific rather than general.

**2. Structured instruction format**

Tülu 3 uses consistent chat-template formatting (system + user + assistant turns) across
all training pairs. I use the Qwen2.5 chat-template (`<|im_start|>system/user/assistant
<|im_end|>`) for the same reason: the model's instruction-following capabilities are tied
to its pre-training token format, and SFT pairs that deviate from this format produce
degraded outputs.

**3. Learning rate for LoRA on instruction-following tasks**

Tülu 3's reported LoRA SFT learning rate of 2e-4 is adopted directly. Their ablation shows
that LR values above 5e-4 produce instability on small LoRA ranks (r≤16) while values
below 1e-4 converge too slowly for short training budgets.

---

## Design Choices I Did Not Adopt

**DPO/RLVR preference optimization stage**

Tülu 3's downstream performance gains primarily come from DPO applied after SFT. However,
Tülu 3's DPO experiments are all on 8B+ models. The paper does not report DPO results for
sub-1B models, and the theoretical argument for why preference optimization should work
(the model needs sufficient capacity to represent the preference distribution across two
competing completions) does not hold at 0.5B. Running DPO on 0.5B with 221 pairs would
introduce noise, not signal. A v0.2 experiment on Qwen2.5-1.5B could add DPO after SFT
convergence is confirmed.

**Data mixture across multiple task types**

Tülu 3 trains on a mixture of instruction types (coding, math, instruction following,
safety). My domain is single-task (B2B outreach emails). Multi-task mixing improves
general capability but is not appropriate here because (a) I lack training data for other
tasks and (b) mixing would dilute the style signal that the adapter is learning.

---

## Key Quote

> "We find that a carefully curated SFT mix of ~326K examples — approximately 5% of the
> full pool considered — outperforms training on the full pool by a significant margin
> on held-out evaluations. Quality filtering is not just efficient; it is necessary."
> — Lambert et al. (2024), §4.2

This directly supports the decision to discard the 12 failing tasks rather than include
them with lower weight.

---

## Limitations of This Paper for My Use Case

- Tülu 3 operates at 8B–70B scale. All quantitative claims (loss curves, DPO gains, task
  performance) are on models at least 16× larger than my 0.5B backbone. Extrapolation is
  qualitative, not quantitative.
- Tülu 3's quality filter is human-validated on diverse tasks. My filter is domain-specific
  and programmatic — it measures rubric compliance, not general quality.
- The Tülu 3 data pipeline is not fully open-source; some filtering steps are described
  qualitatively. I cannot reproduce their exact pipeline, only their principle.
