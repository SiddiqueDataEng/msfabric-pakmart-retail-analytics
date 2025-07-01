"""
pipeline.py – Orchestrator.  Wires config → backend → upload → report.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from config import PipelineConfig
from uploader import (
    ExplorerUploader,
    SDKUploader,
    UploadReport,
    build_tasks,
)

logger = logging.getLogger(__name__)


def run_pipeline(
    mode: str,
    tables: Optional[List[str]] = None,
    years:  Optional[List[int]]  = None,
    cfg:    Optional[PipelineConfig] = None,
    dry_run: bool = False,
) -> UploadReport:
    """
    Execute the upload pipeline.

    Parameters
    ----------
    mode     : full | incremental | dimensions | fact | table:<name>[:<year>]
    tables   : restrict dimensions to these table names
    years    : restrict fact_sale to these years
    cfg      : PipelineConfig (built from env if None)
    dry_run  : print file list, do nothing
    """
    if cfg is None:
        cfg = PipelineConfig()

    tasks = build_tasks(cfg, mode, tables=tables, years=years)

    if not tasks:
        logger.warning("No files matched — nothing to upload.")
        return UploadReport()

    # ── Dry run ───────────────────────────────────────────────────────────────
    if dry_run:
        print(f"\n[DRY RUN]  mode={mode}  backend={cfg.upload_backend}  "
              f"tables={tables}  years={years}")
        print(f"\n  {'LOCAL FILE':<62}  REMOTE PATH")
        print("  " + "-" * 110)
        for t in tasks:
            print(f"  {str(t.local_path):<62}  {t.remote_path}")
        print(f"\n  Total: {len(tasks)} file(s) would be uploaded.")
        return UploadReport()

    # ── Banner ────────────────────────────────────────────────────────────────
    print(f"\n[pipeline] Backend  : {cfg.upload_backend.upper()}")
    print(f"[pipeline] Mode     : {mode}")
    if tables:
        print(f"[pipeline] Tables   : {tables}")
    if years:
        print(f"[pipeline] Years    : {years}")

    # ── Dispatch to the right backend ─────────────────────────────────────────
    if cfg.upload_backend == "explorer":
        print(f"[pipeline] Explorer : {cfg.explorer_files_root}")
        uploader = ExplorerUploader(cfg)

    else:  # sdk
        from auth import get_credential
        print(f"[pipeline] Auth     : {cfg.auth_method}")
        print(f"[pipeline] Workspace: {cfg.workspace_id}")
        print(f"[pipeline] Lakehouse: {cfg.lakehouse_id}")
        credential = get_credential(cfg)
        uploader = SDKUploader(cfg, credential)

    report = uploader.upload(tasks)
    report.print_summary()
    return report
