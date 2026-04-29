# Variation Generation Prompt

**Source:** `generation_scripts/multi_llm_synthesis.py` — `VARIATION_PROMPT`  
**Model:** Qwen 3-8B (dev-tier, via OpenRouter)  
**Purpose:** Generate task variations from passing seeds by changing surface details while preserving dimension and failure mode.

---

## Prompt Template

```
Given this benchmark task seed, write ONE variation by changing only:
- The company name and company_size
- One signal detail (different keyword or number)
- Difficulty may stay the same or drop to "medium"

Keep all string values under 25 words. Keep the same dimension and failure_mode_targeted.

Seed task:
{seed_task}

Output ONLY a single JSON object with the same structure as the seed. No array, no explanation.
```

## Design Notes

- Qwen generates variations for seeds produced by Claude (rotation policy — see `synthesis_memos/memo_llm_as_judge.md`)
- Model may return a single object or a 1-element array; both are handled in `generate_variations()`
- Variations inherit `parent_seed_index` in metadata for provenance tracking
- 5 variations per seed targeted; actual count varies by parse success rate
