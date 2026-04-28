# Audit Memo — Tenacious-Bench v0.1

**Author:** [Your name]  
**Date:** [Fill in]  
**Status:** Draft — complete before Wednesday 21:00 UTC

> Max 600 words. Answer one question: what does τ²-Bench retail (or any public benchmark)
> fail to grade about Tenacious-specific behavior, and what does your Week 10 evidence prove
> about that gap? Reference at least 8 probe IDs and 5 trace IDs.

---

## The Gap

[Write 2-3 sentences identifying the core gap between public benchmarks and Tenacious-specific needs.]

Example structure:
> τ²-Bench retail evaluates generic task completion — can the agent send an email, look up a company.
> It does not measure whether the email sounds like Tenacious wrote it, whether the outreach is
> grounded in the specific hiring signal, or whether the agent correctly represents bench capacity.

---

## Evidence From Week 10

The following Week 10 traces demonstrate the gap concretely:

| Trace ID | What Failed | Why Public Benchmarks Miss It |
|----------|-------------|-------------------------------|
| trace-XXXX | [describe failure] | [why generic benchmark can't catch this] |
| trace-XXXX | | |
| trace-XXXX | | |
| trace-XXXX | | |
| trace-XXXX | | |

Probe IDs from my probe library that map to these failures:
- probe-001: [description]
- probe-002: [description]
- probe-003: [description]
- probe-004: [description]
- probe-005: [description]
- probe-006: [description]
- probe-007: [description]
- probe-008: [description]

---

## What Tenacious-Bench Must Measure

Based on this evidence, the benchmark must evaluate:

1. **Tone preservation** — does the output follow the Tenacious style guide (zero banned phrases, 5 tone markers)?
2. **Signal grounding** — does the outreach reference the specific hiring signal in the brief?
3. **Bench commitment accuracy** — does the agent make promises the bench can actually deliver?
4. **Prospect qualification** — does the agent correctly qualify or disqualify based on company profile?
5. **Discovery call booking** — does the output include a working calendar link and clear CTA?
6. **Objection handling** — for multi-turn tasks, does the agent respond correctly to common objections?

---

## Why Existing Benchmarks Fall Short

[1-2 paragraphs. Be specific about τ²-Bench retail or another benchmark you looked at.
Cite at least one finding from your Required Reading synthesis memos.]

---

## Conclusion

[1 paragraph. State what the new benchmark must do differently and why it matters for Tenacious.]
