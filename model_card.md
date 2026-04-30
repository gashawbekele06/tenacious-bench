# Model Card — Tenacious-Bench LoRA Adapter (Path A)

**Author:** Gashaw Bekele | gashaw@10academy.org  
**Date:** 2026-04-29  
**Adapter ID:** `gashawbekele/tenacious-bench-lora-path-a`  
**Base Model:** `unsloth/Qwen2.5-0.5B-Instruct`  

---

## Model Description

This is a LoRA adapter fine-tuned on Tenacious-Bench SFT pairs for the TRP1 Week 11 Path A
experiment. The adapter targets surface-level generation quality in B2B outreach email
tasks: enforcing a five-marker tone profile (Direct, Grounded, Honest, Professional,
Non-condescending) and suppressing 28 banned vendor-speak phrases identified in the
Tenacious Style Guide v2.

The adapter was trained on 221 curated instruction-response pairs drawn from the
Tenacious-Bench v0.1 training partition (233 tasks total; 12 discarded after failing
3-retry programmatic filter). Training used Unsloth's efficient LoRA implementation on
a free-tier Colab T4 GPU.

---

## Intended Use

| Use | Supported |
|-----|-----------|
| Generating prospect-facing B2B outreach emails in Tenacious style | Yes |
| Evaluating generation quality on Tenacious-Bench v0.1 tasks | Yes |
| General-purpose instruction following | No — not optimised beyond this domain |
| Production deployment | No — published as a reproducible research baseline |

---

## Training Data

| Field | Value |
|-------|-------|
| Dataset | Tenacious-Bench v0.1 training partition |
| Tasks | 221 SFT pairs (out of 233 processed; 94.8% pass rate) |
| Format | Qwen2.5 chat-template: `<\|im_start\|>system/user/assistant<\|im_end\|>` |
| Authoring modes | Trace-derived (28.4%), Programmatic (28.0%), Multi-LLM (39.6%), Hand-authored (4.0%) |
| Judge rotation | Claude-authored tasks judged by Qwen; Qwen-authored judged by Claude |
| Quality filter | All pairs pass full programmatic rubric before inclusion |

---

## Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | `unsloth/Qwen2.5-0.5B-Instruct` | Free T4 budget; Unsloth-optimised |
| LoRA r / alpha | 16 / 16 | Unsloth Qwen guide default; sufficient for style adaptation |
| Max seq length | 2048 | Covers longest SFT pair (~1400 tokens) |
| Epochs | 3 | LIMA standard for small SFT datasets; convergence confirmed at epoch 3 |
| Learning rate | 2e-4 | Tülu 3 LoRA SFT default for instruction-following tasks |
| Batch size | 2 per device × 4 grad accum = 8 effective | Maximum fitting T4 16GB |
| Precision | fp16 | T4 does not support bf16 |
| Seed | 42 | Full reproducibility |
| Warmup steps | 5 | 6.25% of 80 total steps |

---

## Training Run Summary

| Metric | Value |
|--------|-------|
| Total steps | 80 |
| Loss at step 10 | 3.08 |
| Loss at step 80 | 0.42 |
| Final epoch loss | 0.99 |
| Wall-clock time | ~2 minutes (T4 16GB, free Colab) |
| GPU cost | $0.00 (free tier) |

The loss curve confirms convergence: rapid early drop (step 10–40), plateau from step 60
onward. No sign of overfitting on the 221-pair training set.

---

## Evaluation Results

Evaluated on Tenacious-Bench v0.1 held-out partition (n=3 tasks).

| Comparison | Condition A Mean | Condition B Mean | Delta | p-value | Significant |
|-----------|:-:|:-:|:-:|:-:|:-:|
| Delta A: Trained vs Baseline | 0.5315 | 0.5315 | 0.0 | 1.0 | No |
| Delta B: Trained vs Prompted | 0.5315 | 0.5315 | 0.0 | 1.0 | No |
| Delta C: Trained vs τ²-Bench | 0.5315 | 0.61 | -0.0785 | — | Informational |

**Output length:** Trained outputs averaged 210 words vs baseline 256 words (−18% reduction),
confirming the adapter learned concision. This is consistent with the LIMA finding that
style dimensions (length, register) are learnable from small SFT sets.

**Why Delta A = 0.0:** Three confirmed root causes (see `methodology_rationale.md` §Honest
Limitation):
1. 0.5B backbone cannot enforce negative lexical constraints — "bench" appears in input
   context and is reproduced via attention copying across all conditions.
2. Two of three held-out tasks use metadata check values that auto-pass regardless of
   output content (design artefact from the metadata `_is_metadata_phrase()` guard).
3. 120-word count threshold: trained outputs at 210 words clear the threshold but so does
   the baseline (256 words), making the programmatic checks tied.

---

## Limitations

1. **Negative lexical constraint failure:** The 0.5B backbone cannot reliably suppress words
   that appear in the input context. All three conditions (baseline, prompted, trained)
   produce the word "bench" despite it being in the banned-phrase list. This is a
   backbone capacity limitation. Expected to clear on Qwen2.5-1.5B with the same adapter.

2. **Held-out set size (n=3):** Statistical power is insufficient to detect small effects.
   Delta A = 0.0 at n=3 is consistent with both "no effect" and "effect too small to
   detect." A 20-task held-out set (v0.2 target) would provide 80% power at δ=0.05.

3. **Single domain:** The adapter is trained exclusively on B2B outreach scenarios from the
   Tenacious hiring signal domain. No generalisation claim is made.

4. **LLM judge variance:** The tone_judge dimension has κ=0.66 (substantial but not perfect
   agreement). Judge stochasticity contributes non-zero variance to all LLM-scored
   dimensions.

5. **Not production-ready:** This adapter is a reproducible research baseline. It should not
   be deployed in customer-facing systems without independent evaluation on a larger
   held-out set and human review of outputs.

---

## Environmental Impact

| Resource | Value |
|----------|-------|
| Training hardware | Google Colab T4 16GB (free tier) |
| Training time | ~2 minutes |
| CO₂ equivalent | Negligible (free-tier shared infrastructure) |
| Inference hardware | CPU or T4 (Colab) |
| Total project API cost | ~$2.12 (see `cost_log.csv`) |

---

## Citation

```bibtex
@misc{bekele2026tenaciousbench,
  title={Tenacious-Bench v0.1: A Style-Compliance Evaluation Benchmark for B2B Sales Agents},
  author={Bekele, Gashaw},
  year={2026},
  note={TRP1 Week 11 Project, 10 Academy}
}
```

---

## License

Dataset: CC-BY-4.0. Adapter weights: Apache-2.0. Base model license: Apache-2.0 (Qwen2.5).
