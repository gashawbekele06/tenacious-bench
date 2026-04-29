"""
update_rubrics.py

Updates all dev (and optionally train) task JSON files to align rubrics with
Tenacious Style Guide v2:
  1. Extends banned-phrase check_value with the complete Style Guide list
  2. Adds "bench" to every not_contains banned-phrase check
  3. Adds a word_count dimension to cold-outreach tasks (weight 0.05,
     taken equally from the other dimensions so weights still sum to 1.0)
  4. Updates ground_truth.banned_phrases list to match

Run:
    python update_rubrics.py --dirs tenacious_bench_v0.1/dev/
    python update_rubrics.py --dirs tenacious_bench_v0.1/dev/ tenacious_bench_v0.1/train/
"""

import argparse
import json
from pathlib import Path

# -----------------------------------------------------------------------
# Canonical banned phrase check_value (Style Guide v2, complete list)
# -----------------------------------------------------------------------
CANONICAL_BANNED = (
    "hope this finds you well"
    "|just following up"
    "|circling back"
    "|circle back"
    "|touch base"
    "|synergy"
    "|synergize"
    "|leverage"
    "|ecosystem"
    "|world-class"
    "|top talent"
    "|A-players"
    "|rockstar"
    "|ninja"
    "|wizard"
    "|skyrocket"
    "|supercharge"
    "|game-changer"
    "|disruptor"
    "|paradigm shift"
    "|best-in-class"
    "|reach out"
    "|Quick question"
    "|Quick chat"
    "|Don't miss out"
    "|You'll regret"
    "|Per my last email"
    "|bench"
)

CANONICAL_BANNED_LIST = [p.strip() for p in CANONICAL_BANNED.split("|")]

# Names of rubric dimensions that are banned-phrase (not_contains) checks.
BANNED_PHRASE_DIM_NAMES = {
    "banned_phrase_check",
    "no_defensive_language",
    "no_doubling_down",
    "no_overcommit",
    "no_false_price_claim",
    "no_false_ml_assumption",
    "no_outreach_sent",
    "no_hard_gate",
    "no_generic_acknowledgment",
}

# Dimensions that are purely about NOT generating a sales email at all —
# don't inject the sales banned phrases into these.
SKIP_INJECT = {"no_outreach_sent"}

# Word limit for cold outreach tasks (source_mode != multi-turn)
COLD_WORD_LIMIT = 120


def merge_banned_phrases(existing: str) -> str:
    """Merge existing pipe-separated phrases with the canonical list, dedup."""
    existing_phrases = {p.strip().lower() for p in existing.split("|") if p.strip()}
    merged = list(existing_phrases)
    for phrase in CANONICAL_BANNED_LIST:
        if phrase.lower() not in existing_phrases:
            merged.append(phrase)
    return "|".join(merged)


def is_cold_outreach(task: dict) -> bool:
    """True if this is a single-turn cold outreach task (no prior_thread)."""
    return "prior_thread" not in task.get("input", {})


def task_has_word_count_dim(task: dict) -> bool:
    for dim in task.get("rubric", {}).get("dimensions", []):
        if dim.get("check_type") == "word_count":
            return True
    return False


def update_task(task: dict) -> tuple[dict, list[str]]:
    """
    Apply all Style Guide v2 rubric updates to a task.
    Returns (updated_task, list_of_change_descriptions).
    """
    changes = []
    rubric = task.get("rubric", {})
    dims = rubric.get("dimensions", [])

    # 1. Update banned-phrase not_contains dimensions
    for dim in dims:
        name = dim.get("name", "")
        if name in SKIP_INJECT:
            continue
        if dim.get("check_type") == "not_contains" and name in BANNED_PHRASE_DIM_NAMES:
            old_val = dim.get("check_value", "")
            new_val = merge_banned_phrases(old_val)
            if new_val != old_val:
                dim["check_value"] = new_val
                changes.append(f"extended banned phrases in '{name}'")

    # 2. Add word_count dimension to cold-outreach tasks
    if is_cold_outreach(task) and not task_has_word_count_dim(task):
        # Redistribute 0.05 weight from existing dimensions proportionally
        donate = 0.05
        total = sum(d["weight"] for d in dims)
        if total > 0:
            for dim in dims:
                dim["weight"] = round(dim["weight"] - donate * (dim["weight"] / total), 4)
        dims.append({
            "name": "word_count_check",
            "weight": round(donate, 4),
            "check_type": "word_count",
            "description": (
                f"Cold outreach body must be <= {COLD_WORD_LIMIT} words "
                "(Style Guide v2 formatting constraint)."
            ),
            "check_value": str(COLD_WORD_LIMIT),
        })
        # Re-normalise so weights sum exactly to 1.0
        total_new = sum(d["weight"] for d in dims)
        if abs(total_new - 1.0) > 0.001:
            delta = 1.0 - total_new
            dims[-2]["weight"] = round(dims[-2]["weight"] + delta, 4)
        changes.append(f"added word_count_check (max {COLD_WORD_LIMIT} words)")

    # 3. Sync ground_truth.banned_phrases list
    gt = task.get("ground_truth", {})
    existing_gt = set(p.lower() for p in gt.get("banned_phrases", []))
    canonical_lower = set(p.lower() for p in CANONICAL_BANNED_LIST)
    missing_gt = [p for p in CANONICAL_BANNED_LIST if p.lower() not in existing_gt]
    if missing_gt:
        gt["banned_phrases"] = sorted(
            set(gt.get("banned_phrases", []) + missing_gt),
            key=str.lower
        )
        changes.append(f"added {len(missing_gt)} phrases to ground_truth.banned_phrases")

    task["rubric"]["dimensions"] = dims
    return task, changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dirs", nargs="+", required=True, help="Directories to update")
    parser.add_argument("--dry_run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    total_files = 0
    total_changed = 0

    for d in args.dirs:
        for p in sorted(Path(d).glob("*.json")):
            with open(p, encoding="utf-8") as f:
                task = json.load(f)
            if "task_id" not in task:
                continue

            updated, changes = update_task(task)
            total_files += 1

            if changes:
                total_changed += 1
                print(f"{p.name}: {', '.join(changes)}")
                if not args.dry_run:
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(updated, f, indent=2, ensure_ascii=False)
            else:
                print(f"{p.name}: no changes needed")

    print(f"\nProcessed {total_files} tasks, updated {total_changed}")


if __name__ == "__main__":
    main()
