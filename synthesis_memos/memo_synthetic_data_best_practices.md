# Synthesis Memo — Synthetic Data Best Practices

**Paper:** Liu et al. (2024) "Best Practices and Lessons Learned on Synthetic Data for Language Models" (COLM 2024)
**Author:** Gashaw Bekele
**Date:** 2026-04-28
**Status:** Final

---

## Core Argument

Liu et al. survey the landscape of synthetic data use in LLM training and evaluation, synthesising lessons across instruction tuning, alignment, reasoning, and benchmark construction. Their central argument is that synthetic data quality gates downstream model quality far more than quantity: a small set of high-quality, diverse examples outperforms a large low-quality one, and contamination between the generating model and the training pipeline is the primary threat to validity. They identify four recurring failure modes: **mode collapse** (the generating LLM defaults to a narrow output distribution), **quality drift** (later-generated examples are worse than early ones as the model regresses to its prior), **self-referential circularity** (the model trained on synthetic data is evaluated by the model that generated it), and **topic skew** (some task types are over-represented because they are easier for the generating LLM to produce).

---

## Three Design Choices Relevant to Tenacious-Bench

1. **Judge rotation to prevent self-referential circularity.** Liu et al. identify this as the primary quality threat when synthetic data is used for fine-tuning. `generation_scripts/judge_filter.py` implements a rotation policy enforced by `pick_judge_model()`: Claude-generated tasks are judged by Qwen; Qwen-generated tasks are judged by Claude. Trace-derived and programmatic tasks auto-pass because they are not LLM-generated and cannot suffer from this failure mode.

2. **Quality gate before quantity target.** Liu et al. recommend setting a quality floor and generating until the floor is met rather than generating N examples and filtering down. Our pipeline generates seeds, filters through the inline judge, then generates variations only from passing seeds — matching this recommendation. The 185/189 pass rate on the judge filter is the quality gate; the remaining 4 failures were discarded rather than included.

3. **Dimension rotation to counter topic skew.** Liu et al. recommend diversity sampling to prevent the generating model from defaulting to its natural attractor. We implement forced dimension rotation in `multi_llm_synthesis.py`: each seed is assigned a target dimension by modular index (`dimensions[i % 8]`) with an explicit instruction appended to the prompt.

---

## Where I Disagree With the Paper

**Paper's recommendation:** Liu et al. (Section 3.2) recommend random sampling across task types as the primary mechanism for achieving diversity, arguing that constrained generation introduces the generating model's priors about what "canonical" examples of each type look like.

**My choice:** Tenacious-Bench uses forced dimension rotation — each seed is assigned a target dimension by modular index and the prompt appends an explicit override: `IMPORTANT: You MUST set "dimension" to "{target_dim}"`. This is a constraint, not random sampling.

**Justification:** Random sampling failed in our actual pipeline. The first 20 seeds generated without the rotation constraint all came back as "signal-grounding" — the LLM's natural attractor for B2B sales tasks, because the majority of sales outreach training data in the model's corpus involves referencing hiring signals. Dimensions like "bench-commitment-accuracy," "cost-accuracy," and "multi-turn-coherence" appeared in zero of the first 20 seeds despite being listed in the prompt. This is exactly the topic skew Liu et al. warn about, but it is caused by the generating model's training distribution rather than by our prompt design — random sampling over a model with a strong prior toward signal-grounding tasks does not produce uniform diversity, it samples from a skewed distribution. The rotation constraint forces generation against the prior, which is the only reliable path to representation in the dimensions that map to our highest-trigger-rate failure modes: P-011 (0.44, objection-handling) and P-010 (0.38, tone-preservation) would both have been underrepresented without it. The cost is exactly what Liu et al. predict — some constrained outputs are lower quality than the model would have produced freely — which is why the inline judge filter exists to cull them.

---

## One Insight I Am Directly Applying

Liu et al.'s observation that **model collapse is detectable by measuring output entropy across task types** — when entropy drops below a threshold, the generating model has converged to a narrow distribution — is the diagnostic I would apply in a v0.2 pipeline audit. In v0.1, I detected the collapse empirically by observing that all 20 seeds mapped to "signal-grounding" before adding the rotation constraint. In v0.2, computing the dimension entropy of generated seeds before proceeding to variation generation would catch collapse earlier and allow the rotation constraint to be applied dynamically rather than statically hardcoded at the prompt level.
