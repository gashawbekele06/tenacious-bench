# Synthesis Memo — Zhou et al. (2023): LIMA

**Author:** Gashaw Bekele  
**Date:** 2026-04-29  
**Paper:** Zhou et al. (2023). "LIMA: Less Is More for Alignment."  
**Relevance:** SFT dataset size justification and format diversity strategy  

---

## Core Claim

LIMA demonstrates that alignment is primarily a **surface learning problem**, not a
knowledge acquisition problem. A base LLM already contains the knowledge needed to
respond helpfully; SFT teaches the model the format and register in which to express
that knowledge. As a direct consequence, 1,000 carefully curated instruction-response
pairs are sufficient to produce a well-aligned model — volume beyond this threshold
adds diminishing returns relative to quality.

---

## Design Choices I Adopted

**1. Dataset size in the LIMA sufficiency range**

My 221 SFT pairs are within LIMA's demonstrated sufficiency range (1,000 pairs for a 7B
model; the appropriate scale for a 0.5B model is expected to be smaller, not larger, since
there is less representational capacity to fill). LIMA shows that 1,000 is an upper bound
for alignment on general tasks; for narrow domain tasks with low lexical diversity (B2B
outreach emails), 200–300 pairs should be sufficient to shift the surface register without
overfitting.

**2. Format and topic diversity over volume**

LIMA's secondary finding is that **diversity of format and topic** matters more than raw
count. Their 1,000 pairs span coding, reasoning, creative writing, factual recall, and
multi-turn dialogue — and this diversity explains much of the alignment gain. I implement
a four-mode authoring pipeline (trace-derived, programmatic, multi-LLM synthesis,
hand-authored) specifically to ensure the 221 pairs cover all 8 failure dimensions from
qualitatively different generation paths. Mode diversity is the domain analog of LIMA's
format diversity.

**3. 3-epoch training standard**

LIMA trains for 3 epochs and reports that additional epochs produce marginal improvement
and occasional overfitting on small SFT sets. I use the same 3-epoch schedule. The loss
curve (3.08 at step 10 → 0.42 at step 80, epoch 3 final loss 0.99) is consistent with
LIMA's reported convergence pattern for small aligned datasets.

---

## Design Choices I Did Not Adopt — One Informed Disagreement

**Source corpus: pre-existing human-curated data vs. Magpie-style self-instruction**

LIMA draws its 1,000 pairs from existing human-generated corpora: StackExchange, wikiHow,
SuperNI, and manually crafted examples. The implicit assumption is that a high-quality
human corpus exists for the target domain.

My domain — B2B outreach emails for technical staffing, with specific signal grounding
requirements — has no such corpus. There is no StackExchange thread for "how to write a
prospect-facing email using the Tenacious style guide when the hiring signal is a 12-ML
role posting on LinkedIn." The Magpie-style self-instruction approach is therefore
necessary as a substitute, not a supplement. This is not a departure from LIMA's
principle (quality + diversity over volume) but from its data sourcing assumption.

---

## Key Quote

> "Alignment can be a simple process. If a model has been pretrained on enough knowledge,
> then aligning it to follow instructions primarily requires teaching it the style of
> communication rather than new factual knowledge. We find that 1,000 such examples is
> sufficient."
> — Zhou et al. (2023), §1

This is the most direct support for the core Path A hypothesis: the Week 10 failures are
surface-level register failures, not knowledge failures. The model knows what a good
outreach email is; it defaults to the wrong register. SFT teaches the right one.

---

## Limitations of This Paper for My Use Case

- LIMA operates on LLaMA-65B and LLaMA-7B. The 1,000-pair claim is calibrated to 7B+
  models. At 0.5B, the model may not have enough representational capacity to fully absorb
  the style signal from 221 pairs.
- LIMA's pairs are human-authored from curated corpora. My pairs are LLM-generated and
  programmatically filtered. LLM-generated pairs may have systematic biases (e.g., all
  gold outputs share the LLM teacher's style) that human-curated data does not.
- LIMA does not test negative lexical constraints (banned phrases). The surface-learning
  claim is about positive stylistic features; whether 0.5B SFT can suppress specific
  tokens is a separate empirical question that LIMA does not address.
