# Synthesis Memo — Xu et al. (2024): Magpie

**Author:** Gashaw Bekele  
**Date:** 2026-04-29  
**Paper:** Xu et al. (2024). "Magpie: Alignment Data Synthesis from Scratch via Self-Synthesis of an Aligned LLM."  
**Relevance:** SFT pair generation pipeline design (`generate_sft_pairs.py`)  

---

## Core Claim

Magpie demonstrates that aligned LLMs can generate their own high-quality alignment data
without any seed examples, human annotation, or curated corpora. By prompting a model
with only the system-turn prefix and allowing it to auto-regressively complete both the
user instruction and the assistant response, Magpie produces instruction-response pairs
whose quality, as measured by automated judges and downstream fine-tuning performance,
matches or exceeds manually curated datasets like Alpaca and ShareGPT at scale.

---

## Design Choices I Adopted

**1. LLM-driven pair generation with automated quality filtering**

Magpie's core pipeline: (1) prompt the model with the system turn only, (2) let it generate
a user instruction, (3) let it generate an assistant response, (4) score the pair with an
automated judge, (5) discard failing pairs. I implement this in `generate_sft_pairs.py`:
the SYSTEM_PROMPT encodes the Tenacious style guide; the model is prompted to generate a
gold-standard outreach email for a given task context; the output is scored against the
full programmatic rubric; failing outputs are retried up to 3 times and discarded if they
do not pass.

**2. Automated quality filtering as a hard gate**

Magpie applies automated quality scoring as a hard inclusion/exclusion gate, not a soft
weight. Pairs below the quality threshold are removed entirely, not down-weighted. I follow
the same convention: 12 tasks were discarded (not down-weighted) because they failed after
3 retries. This ensures the training set is clean rather than noisy.

**3. Teacher model choice**

Magpie uses the same model family for generation and downstream fine-tuning (LLaMA-3-8B
generates pairs that are used to fine-tune LLaMA-3-8B). I use Claude Haiku as the teacher
model (for SFT pair generation) and fine-tune Qwen2.5-0.5B. This is a cross-family
setup that Magpie does not test but that is consistent with the principle: the teacher
provides a gold-standard style reference that the student model learns from.

---

## Key Departure from Vanilla Magpie

**Structured input fields instead of zero-shot prompting**

Vanilla Magpie prompts the model with nothing (just the system-turn prefix) and relies on
the model to self-generate both the instruction and the response. This works for general
alignment because the model has seen diverse instruction types during pre-training.

My domain requires **signal grounding**: a valid outreach email for a specific task must
reference a specific hiring signal (e.g., "NeuralCart posted 12 ML roles 60 days ago"),
a specific bench candidate profile, and a specific prospect profile. These cannot be
self-generated without access to the actual signal data.

I therefore provide three structured input fields in the task context:
- `hiring_signal_brief`: the signal that triggered the task
- `bench_summary`: the candidate being matched
- `prospect_profile`: the decision-maker being targeted

The model generates only the assistant response (the outreach email), not the instruction.
This is a constrained version of Magpie — closer to instruction-tuning than pure
self-synthesis — but it is the appropriate adaptation for a grounded domain task.

---

## Key Quote

> "Magpie requires no seed examples, no human annotation, and no curated data sources.
> The aligned model is its own best teacher."
> — Xu et al. (2024), §1

This supports using Claude Haiku as the SFT pair generator: as a well-aligned model, it
serves as a gold-standard teacher for the Tenacious style, given the style guide as its
system prompt. The model's alignment is the quality guarantee that replaces human
annotation.

---

## Limitations of This Paper for My Use Case

- Magpie's quality results are measured on general benchmarks (AlpacaEval, MT-Bench).
  These do not measure domain-specific style compliance. Whether Magpie-generated pairs
  are sufficient for learning banned-phrase suppression is not addressed by the paper.
- Magpie uses the same model for generation and fine-tuning (LLaMA-3-8B → LLaMA-3-8B).
  Cross-family distillation (Claude Haiku → Qwen2.5-0.5B) may introduce a capability gap:
  the student may not have the representational capacity to reproduce the teacher's outputs
  exactly, particularly for negative lexical constraints.
- Magpie's automated filter is a reward model score. My filter is a programmatic rubric.
  The two are not directly comparable. A reward model score penalizes style broadly;
  a programmatic rubric penalizes specific violations. For my domain, the programmatic
  filter is more appropriate, but it may pass pairs with non-obvious style violations that
  a reward model would catch.
