"""Standalone report generation: ``python -m pipeline.report <repo> [--no-draft]``.

Reads output/<repo>/ artifacts, writes output/<repo>/report_data.json + REPORT.md.
``<repo>`` is a repo URL/path (resolved to its run-dir name) or the run-dir name itself.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.cli import load_dotenv, repo_name
from pipeline.config import DEFAULT
from pipeline.report.build import build


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pipeline.report")
    p.add_argument("repo", help="repo URL/path or output/<name> run-dir name")
    p.add_argument("--no-draft", action="store_true", help="skip the BIG narrative draft")
    p.add_argument("--output-root", default="output")
    args = p.parse_args(argv)

    root = Path(args.output_root)
    run_dir = root / args.repo
    if not run_dir.is_dir():
        run_dir = root / repo_name(args.repo)
    if not run_dir.is_dir():
        raise SystemExit(f"no run dir under {root}/ for {args.repo!r}")

    llm = None
    if not args.no_draft:
        load_dotenv()
        from pipeline.llm.client import LLMClient

        llm = LLMClient(
            config=DEFAULT,
            stage="report",
            audit_dir=run_dir / "audit",
            transcripts_dir=Path("transcripts"),
        )
    data_path, md_path = build(run_dir, DEFAULT, llm=llm, draft=not args.no_draft)
    print(f"wrote {data_path} and {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
