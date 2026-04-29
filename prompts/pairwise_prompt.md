# Pairwise Judge Prompt

**Source:** `generation_scripts/judge_filter.py` — `PAIRWISE_PROMPT`  
**Model:** OpenRouter dev-tier (default)  
**Purpose:** Compare two tasks targeting the same failure mode; selects the more diagnostic one for dataset inclusion when deduplication candidates are near-equal in quality.

---

## Prompt Template

```
Two benchmark tasks target the same failure mode. Which is MORE DIAGNOSTIC — i.e., harder to solve by a generic agent, more grounded in realistic B2B sales behavior?

Task A:
{task_a}

Task B:
{task_b}

Output ONLY: {"winner": "A" or "B", "reasoning": "<one sentence>"}
```

## Usage

Called via `pairwise_compare()` in `judge_filter.py`. Used for spot-checking and tie-breaking when two tasks have identical pointwise scores on the same dimension. Not applied to every task pair — only invoked explicitly.
