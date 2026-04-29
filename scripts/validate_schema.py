"""
scripts/validate_schema.py

Validates one or more task JSON files against schema.json.
Usage:
    python scripts/validate_schema.py --task path/to/task.json
    python scripts/validate_schema.py --example 0       # validate example from schema.json
    python scripts/validate_schema.py --dir tenacious_bench_v0.1/dev/
"""

import argparse
import json
import sys
from pathlib import Path

import jsonschema


def load_schema(schema_path: str = "schema.json") -> dict:
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def validate_task(task: dict, schema: dict) -> list[str]:
    errors = []
    try:
        jsonschema.validate(task, schema)
    except jsonschema.ValidationError as e:
        errors.append(str(e.message))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, help="Path to a single task JSON")
    parser.add_argument("--example", type=int, help="Validate example N from schema.json")
    parser.add_argument("--dir", type=str, help="Validate all .json files in directory")
    parser.add_argument("--schema", default="schema.json")
    args = parser.parse_args()

    schema = load_schema(args.schema)

    if args.example is not None:
        examples = schema.get("examples", [])
        if args.example >= len(examples):
            print(f"No example at index {args.example}")
            sys.exit(1)
        task = examples[args.example]
        errors = validate_task(task, schema)
        if errors:
            print(f"Example {args.example} FAILED:\n" + "\n".join(errors))
            sys.exit(1)
        print(f"Example {args.example}: VALID")

    elif args.task:
        with open(args.task, encoding="utf-8") as f:
            task = json.load(f)
        errors = validate_task(task, schema)
        if errors:
            print(f"FAILED:\n" + "\n".join(errors))
            sys.exit(1)
        print(f"{args.task}: VALID")

    elif args.dir:
        files = sorted(Path(args.dir).glob("*.json"))
        passed, failed = 0, 0
        for p in files:
            with open(p, encoding="utf-8") as f:
                task = json.load(f)
            if "task_id" not in task:
                continue  # skip log files
            errors = validate_task(task, schema)
            if errors:
                print(f"FAIL {p.name}: {errors[0]}")
                failed += 1
            else:
                passed += 1
        print(f"\nValidation complete: {passed} passed, {failed} failed out of {passed+failed} tasks")
        if failed > 0:
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
