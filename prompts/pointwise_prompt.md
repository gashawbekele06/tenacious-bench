# Pointwise Judge Prompt (Standalone Filter)

**Source:** `generation_scripts/judge_filter.py` — `POINTWISE_PROMPT`  
**Model:** Rotated per task synthesis model (see rotation policy)  
**Purpose:** Standalone quality filter for any task directory; used both as primary filter and for spot-checking.

---

## Prompt Template

```
You are a benchmark quality evaluator for B2B sales AI evaluation tasks.

Score this task on three dimensions (1-5 each):

1. input_coherence (1-5): Is the hiring signal brief realistic? Is the prospect profile internally consistent? Would a real B2B sales agent encounter this scenario?
2. ground_truth_verifiability (1-5): Can the ground_truth fields be checked programmatically (regex, string match) without ambiguity? Is the correct answer unambiguous?
3. rubric_clarity (1-5): Is it clear what passes vs fails? Can a different person apply the rubric and get the same score?

Inclusion thresholds: input_coherence >= 3, ground_truth_verifiability >= 4, rubric_clarity >= 3.

Task JSON:
{task}

Output ONLY this JSON (no other text):
{"input_coherence": <1-5>, "ground_truth_verifiability": <1-5>, "rubric_clarity": <1-5>, "reasoning": "<one sentence why this passes or fails>"}
```

## Inclusion Thresholds

| Dimension | Minimum Score |
|-----------|---------------|
| input_coherence | ≥ 3 |
| ground_truth_verifiability | ≥ 4 |
| rubric_clarity | ≥ 3 |

## Judge Rotation Policy

Enforced by `pick_judge_model()` in `judge_filter.py`:

| Synthesis model | Judge |
|----------------|-------|
| Claude / Anthropic-class | Qwen 3-8B (OpenRouter) |
| Qwen / OpenRouter dev-tier | Claude Haiku 4.5 (Anthropic) |
| None (trace-derived, programmatic) | Auto-pass |
