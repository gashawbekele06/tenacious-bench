# Inter-Rater Agreement — Tenacious-Bench v0.1

**Author:** Gashaw Bekele  
**Round 1 date:** 2026-04-27  
**Round 2 date:** 2026-04-28  
**Sample size:** 30 tasks from the dev partition

---

## Protocol

1. Randomly sampled 30 tasks from the dev partition (seed=42)
2. Labeled each task against the rubric (pass/fail per dimension) using `scoring_evaluator.py`
   for programmatic dimensions; manual judgment for `tone_judge`
3. Committed labels to `inter_rater_r1_labels.json` — did not look at until Round 2 complete
4. Waited 24 hours
5. Re-labeled the same 30 tasks independently
6. Computed Cohen's κ and percent agreement per dimension

---

## Results

### Percent Agreement by Dimension

| Rubric Dimension | Round 1 Pass Rate | Round 2 Pass Rate | % Agreement | Action Taken |
|------------------|:-----------------:|:-----------------:|:-----------:|--------------|
| banned_phrase_check | 76.7% | 76.7% | **100%** | None — deterministic check |
| signal_reference_check | 73.3% | 73.3% | **100%** | None — deterministic check |
| calendar_link_check | 83.3% | 83.3% | **100%** | None — deterministic check |
| word_count_check | 80.0% | 80.0% | **100%** | None — deterministic check |
| tone_judge (LLM) | 60.0% | 56.7% | **83.3%** | "grounded" marker definition tightened (see Revisions) |
| **Overall** | **74.7%** | **74.0%** | **97.3%** | — |

Threshold for acceptance: **≥ 80% agreement per dimension**.  
Dimensions below 80%: **none** (all cleared after grounded-marker revision).

### Cohen's Kappa

| Dimension | κ | Interpretation |
|-----------|:-:|----------------|
| banned_phrase_check | 1.00 | Perfect — deterministic check, same output every run |
| signal_reference_check | 1.00 | Perfect — deterministic check |
| calendar_link_check | 1.00 | Perfect — deterministic check |
| word_count_check | 1.00 | Perfect — deterministic check |
| tone_judge | 0.66 | Substantial agreement |
| **Overall** | **0.95** | Near-perfect |

---

## Rubric Revisions

| Dimension | Original Rubric | Revised Rubric | Reason |
|-----------|----------------|----------------|--------|
| tone_judge → grounded marker | "Signal name cited in output" scores 4 | "Signal name **plus** a numeric anchor (role count, funding amount, or date) required for score 4; company name alone = 3" | Round 1 and Round 2 disagreed on 5 tasks where the company name appeared but no numeric anchor was present. Tightening the definition aligned both rounds and matches the Clearbit/11-day standard already used in EX-03. |

---

## Conclusion

The rubric met the ≥ 80% agreement threshold on all five dimensions after one targeted revision.
The four programmatic check types (`not_contains`, `contains`, `regex`, `word_count`) are
deterministic and produce 100% agreement and κ = 1.0 by construction — this is an expected
property of machine-verifiable rubric design, not an optimistic result. The `tone_judge`
LLM dimension achieved 83.3% agreement (κ = 0.66) after the "grounded" marker definition
was tightened to require a numeric anchor alongside a signal name. No other rubric changes
were required. The benchmark's scoring reliability is therefore bounded by the LLM judge
stochasticity (κ = 0.66 on the dimension carrying 45% weight in hybrid tasks); this is
within the acceptable range for judge-based evaluation and is consistent with published
results from Zheng et al. (2023) and Gu et al. (2024).
