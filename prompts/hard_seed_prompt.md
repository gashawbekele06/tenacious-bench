# Hard Seed Generation Prompt

**Source:** `generation_scripts/multi_llm_synthesis.py` — `HARD_SEED_PROMPT`  
**Model:** Claude Haiku 4.5 (frontier, via OpenRouter)  
**Purpose:** Generate hard evaluation task seeds anchored to specific Week 10 failure modes.

---

## Prompt Template

```
You are a benchmark designer for B2B sales AI agents.

Tenacious is a staffing company placing pre-vetted engineers. The sales agent writes outreach emails using hiring signals and books discovery calls.

Week 10 failure modes (pick ONE to target):
{failure_taxonomy}

Write ONE hard evaluation task. Keep all string values SHORT (under 30 words each).

Output ONLY this JSON, no explanation:
{
  "dimension": "<tone-preservation|signal-grounding|prospect-qualification|bench-commitment-accuracy|discovery-call-booking|objection-handling|multi-turn-coherence|cost-accuracy>",
  "difficulty": "hard",
  "scenario_description": "<one sentence max>",
  "input": {
    "hiring_signal_brief": "<signal in 20 words max>",
    "bench_summary": "Tenacious: pre-vetted engineers, 2-week deployment.",
    "prospect_profile": {
      "company_name": "<company name>",
      "company_size": "<11-50|51-200|201-500|501-2000>",
      "segment": "<segment label>",
      "requested_headcount": <1-6>,
      "ai_maturity_score": <1.0-4.0>,
      "signal_confidence": <0.5-0.9>
    }
  },
  "ground_truth": {
    "required_signal_references": ["<phrase1>", "<phrase2>"],
    "banned_phrases": ["hope this finds you well", "circle back", "touch base", "synergy", "leverage"],
    "required_elements": ["calendar_link", "company_name_mention"],
    "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
  },
  "failure_mode_targeted": "<probe ID and name>"
}
```

## Dimension Rotation Suffix

Appended after the template for each seed `i`:

```
IMPORTANT: You MUST set "dimension" to "{target_dim}" for this task.
```

Where `target_dim = dimensions[i % 8]` and `dimensions` cycles:
`["tone-preservation", "signal-grounding", "prospect-qualification", "bench-commitment-accuracy", "discovery-call-booking", "objection-handling", "multi-turn-coherence", "cost-accuracy"]`

**Rationale:** Without forced rotation, the model defaults all seeds to "signal-grounding" (empirically observed: 20/20 seeds pre-rotation). See `synthesis_memos/memo_synthetic_data_best_practices.md` §"Where I Disagree With the Paper".
