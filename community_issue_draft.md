# GitHub Issue Draft — τ²-Bench / tau2-bench

**Target repo:** `tau-bench` (https://github.com/sierra-research/tau-bench or equivalent)  
**Issue title:** Tenacious-Bench finding: τ²-Bench misses register/style failures in B2B generation agents  
**Prepared:** 2026-04-29  
**Instructions:** Copy the body below and open as a new issue on the τ²-Bench repository.

---

## Issue Body

### Summary

We built Tenacious-Bench v0.1 (250 tasks, 8 dimensions) to evaluate a B2B sales
development agent and found a systematic gap in what τ²-Bench captures: **surface-level
register failures that pass τ²-Bench but fail on domain-specific style compliance**.

We are sharing this finding in case it is useful to the τ²-Bench maintainers and
the community.

### The Gap

τ²-Bench measures task completion: did the agent produce an output, include the required
elements, and respond appropriately to the task structure? For our agent (outreach email
generation), a response that opens with "I completely understand your frustration —
we are different from other offshore vendors" passes τ²-Bench because:
- An email was produced ✓
- The objection (offshore concern) was addressed ✓
- The response was on-topic ✓

But the response fails on the style register that makes outreach emails actually effective:
- Empathy-appeasement language instead of evidence-based displacement ✗
- Vendor-speak ("different from other offshore vendors") ✗
- No specific evidence or numeric anchor ✗

Our probe library confirmed this is systematic: P-011 (offshore-appeasement language)
triggered at 0.44 on structured test inputs — nearly deterministic failure on a specific
register pattern that τ²-Bench would not flag.

### Tenacious-Bench Approach

We added five check types to address this:
1. `not_contains` — banned phrases list (28 phrases, e.g. "best-in-class", "synergize")
2. `contains` — required evidence citations (signal name + numeric anchor)
3. `regex` — structural requirements (calendar links, date formats)
4. `word_count` — concision enforcement
5. `llm_score` — LLM judge scoring against 5 tone markers (Direct, Grounded, Honest,
   Professional, Non-condescending) on a 1–5 scale

The hybrid scoring (programmatic + LLM judge) catches failures that neither approach
alone would detect.

### Key Finding

Path A SFT (LoRA, Qwen2.5-0.5B) with 221 high-quality pairs produced Delta A = 0.0
on our held-out set. Importantly, this was a measurement problem (n=3 held-out,
metadata auto-pass artefact), not a model failure — the adapter did learn concision
(−18% output length reduction) and the loss curve confirmed convergence.

The τ²-Bench score (0.61) and Tenacious-Bench score (0.5315) are measuring different
things. An agent that improves on τ²-Bench may not improve on Tenacious-Bench, and
vice versa.

### Request

We would appreciate feedback on:
1. Whether the τ²-Bench team has seen similar register/style gaps in other domains
2. Whether τ²-Bench has plans to add weighted LLM judge checks for style compliance
3. Whether our contamination-prevention approach (8-gram + cosine similarity check)
   is compatible with τ²-Bench's data pipeline

Dataset: https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1  
Code: https://github.com/gashawbekele06/tenacious-bench  

Thanks for building τ²-Bench — it gave us a solid foundation to identify exactly where
domain-specific style evaluation needs to go beyond task completion.

— Gashaw Bekele (gashaw@10academy.org)
