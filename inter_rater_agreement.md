# Inter-Rater Agreement — Tenacious-Bench v0.1

**Author:** [Your name]  
**Round 1 date:** [Date]  
**Round 2 date:** [Date — must be 24 hours later, without looking at Round 1]  
**Sample size:** 30 tasks from the dev partition

---

## Protocol

1. Randomly sampled 30 tasks from the dev partition (seed=42)
2. Labeled each task against the rubric (pass/fail per dimension)
3. Committed labels to `inter_rater_r1_labels.json` — DO NOT look at until Round 2 is complete
4. Waited 24 hours
5. Re-labeled the same 30 tasks independently
6. Computed agreement statistics

---

## Results

### Percent Agreement by Dimension

| Rubric Dimension | Round 1 Pass Rate | Round 2 Pass Rate | % Agreement | Action Taken |
|------------------|------------------|------------------|-------------|--------------|
| banned_phrase_check | | | | |
| signal_reference_check | | | | |
| calendar_link_check | | | | |
| tone_judge (LLM) | | | | |
| **Overall** | | | | |

Threshold for acceptance: **≥ 80% agreement per dimension**.  
Dimensions below 80%: [list or "none"]

### Cohen's Kappa

| Dimension | κ | Interpretation |
|-----------|---|----------------|
| banned_phrase_check | | |
| signal_reference_check | | |
| calendar_link_check | | |
| tone_judge | | |

---

## Rubric Revisions

*(Document any revisions made as a result of low agreement)*

| Dimension | Original Rubric | Revised Rubric | Reason |
|-----------|----------------|----------------|--------|
| | | | |

---

## Conclusion

[1 paragraph. State whether rubric met the 80% threshold, what changes were made, and
what this implies about the benchmark's reliability.]
