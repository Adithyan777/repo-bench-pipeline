"""`python -m pipeline.validate <task_dir> [<task_dir> ...]` -- run the validation
harness over task folders and print each verdict. Exit 0 iff every task is VALID."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.cli import apply_overrides
from pipeline.config import Config
from pipeline.tasks.harness import validate_tasks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline.validate")
    parser.add_argument("task_dirs", nargs="+", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="section.key=value")
    parser.add_argument("--json", action="store_true", help="print full verdicts as JSON")
    args = parser.parse_args(argv)
    config = Config()
    apply_overrides(config, args.set)
    verdicts = validate_tasks(args.task_dirs, config)
    for path, verdict in verdicts.items():
        status = "VALID" if verdict["valid"] else "INVALID"
        line = f"{status}  {path}"
        if verdict["reasons"]:
            line += "  [" + ", ".join(verdict["reasons"]) + "]"
        print(line)
    if args.json:
        print(json.dumps(verdicts, indent=2, sort_keys=True))
    return 0 if all(v["valid"] for v in verdicts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
