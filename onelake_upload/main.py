#!/usr/bin/env python3
"""
main.py – CLI entry-point for the PakMart → OneLake upload pipeline.

Usage examples
--------------
# Full load (all dimensions + all fact years):
python main.py --mode full

# Full load but only specific tables:
python main.py --mode full --tables dimension_city dimension_customer

# Full load restricted to specific fact years:
python main.py --mode full --years 2021 2022

# Incremental only (2023 data):
python main.py --mode incremental

# Only dimension tables (no fact):
python main.py --mode dimensions

# Only fact_sale files (no dimensions):
python main.py --mode fact

# One specific dimension table:
python main.py --mode table:dimension_stock_item

# One year of fact_sale:
python main.py --mode table:fact_sale:2022

# Dry run – see what would be uploaded without touching OneLake:
python main.py --mode full --dry-run

# Always overwrite (ignore skip_unchanged env setting):
python main.py --mode incremental --force

# Verbose logging:
python main.py --mode full --log-level DEBUG
"""

from __future__ import annotations

import argparse
import logging
import sys
import os

# Allow running directly from this folder
sys.path.insert(0, os.path.dirname(__file__))

from config import PipelineConfig
from pipeline import run_pipeline


# ─────────────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pakmart-upload",
        description="Upload PakMart data to Microsoft Fabric OneLake",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--mode", "-m",
        required=True,
        metavar="MODE",
        help=(
            "Upload mode. Options:\n"
            "  full          – all dimensions + all fact years\n"
            "  incremental   – only the 2023 incremental file\n"
            "  dimensions    – only dimension tables\n"
            "  fact          – only fact_sale year files\n"
            "  table:<name>  – single table, e.g. table:dimension_city\n"
            "  table:fact_sale:<year> – one year, e.g. table:fact_sale:2022"
        ),
    )

    parser.add_argument(
        "--tables", "-t",
        nargs="+",
        metavar="TABLE",
        help=(
            "Restrict dimensions to these table names "
            "(used with --mode full or --mode dimensions)."
        ),
    )

    parser.add_argument(
        "--years", "-y",
        nargs="+",
        type=int,
        metavar="YEAR",
        help=(
            "Restrict fact_sale to these years "
            "(used with --mode full or --mode fact). "
            "Example: --years 2021 2022"
        ),
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print the list of files that would be uploaded without actually uploading.",
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite remote files even when local size == remote size (disables skip_unchanged).",
    )

    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        metavar="N",
        help="Override MAX_WORKERS from .env. Number of parallel upload threads.",
    )

    parser.add_argument(
        "--data-root",
        default=None,
        metavar="PATH",
        help="Override LOCAL_DATA_ROOT from .env. Path to the pakmart_data folder.",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = _build_parser()
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Build config (reads .env / environment)
    # Dry-run skips credential validation so you can preview without a .env
    try:
        from dataclasses import replace as _dc_replace
        cfg = PipelineConfig(_skip_validation=args.dry_run)
    except EnvironmentError as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        sys.exit(1)

    # Apply CLI overrides
    if args.force:
        cfg.skip_unchanged = False
    if args.workers is not None:
        cfg.max_workers = args.workers
    if args.data_root is not None:
        from pathlib import Path
        cfg.local_data_root = Path(args.data_root)

    # Run
    report = run_pipeline(
        mode=args.mode,
        tables=args.tables,
        years=args.years,
        cfg=cfg,
        dry_run=args.dry_run,
    )

    # Exit with error code when any upload failed
    if report.failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
