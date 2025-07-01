"""
uploader.py – Upload engine with two backends.

  ExplorerUploader  – copies files via the locally-mounted OneLake File Explorer.
                      No credentials. Pure shutil.copy2. Fast, simple, reliable.

  SDKUploader       – uploads over HTTPS using azure-storage-file-datalake.
                      Requires Azure credentials.

Both share the same UploadTask / UploadResult / UploadReport data model and
the same build_tasks() function.
"""

from __future__ import annotations

import logging
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shared data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UploadTask:
    local_path: Path
    # Relative path inside the lakehouse/Files/pakmart/ folder
    # e.g. "full/dimension_city/dimension_city.csv"
    remote_path: str
    table_name: str
    load_type: str            # "full" | "incremental"
    file_size_bytes: int = 0

    def __post_init__(self):
        if self.local_path.exists():
            self.file_size_bytes = self.local_path.stat().st_size


@dataclass
class UploadResult:
    task: UploadTask
    success: bool
    skipped: bool = False
    duration_sec: float = 0.0
    error: Optional[str] = None
    bytes_uploaded: int = 0


@dataclass
class UploadReport:
    results: List[UploadResult] = field(default_factory=list)
    backend: str = "unknown"

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success and not r.skipped)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def total_bytes(self) -> int:
        return sum(r.bytes_uploaded for r in self.results)

    @property
    def total_duration(self) -> float:
        return sum(r.duration_sec for r in self.results)

    def print_summary(self):
        mb = self.total_bytes / 1_048_576
        print("\n" + "=" * 60)
        print(f"  UPLOAD REPORT  [{self.backend.upper()} backend]")
        print("=" * 60)
        print(f"  Total files  : {self.total}")
        print(f"  Uploaded     : {self.succeeded}")
        print(f"  Skipped      : {self.skipped}  (unchanged)")
        print(f"  Failed       : {self.failed}")
        print(f"  Data uploaded: {mb:.2f} MB")
        print(f"  Wall time    : {self.total_duration:.1f}s")
        if self.failed:
            print("\n  FAILURES:")
            for r in self.results:
                if not r.success:
                    print(f"    ✗ {r.task.remote_path}  →  {r.error}")
        print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# Task builder  (shared by both backends)
# ─────────────────────────────────────────────────────────────────────────────

DIMENSION_TABLES = [
    "dimension_city",
    "dimension_customer",
    "dimension_date",
    "dimension_employee",
    "dimension_stock_item",
]
FACT_SALE_FULL_DIR = "fact_sale"
INCREMENTAL_DIR    = "fact_sale_1y_incremental"


def build_tasks(
    cfg: PipelineConfig,
    mode: str,
    tables: Optional[List[str]] = None,
    years:  Optional[List[int]]  = None,
) -> List[UploadTask]:
    """
    Resolve the file list for the requested mode.

    Modes
    -----
    full          – all dimensions + all fact years
    incremental   – incremental folder only
    dimensions    – dimension tables only
    fact          – fact year files only  (optional --years filter)
    table:<name>  – single table, e.g. table:dimension_city
    table:fact_sale:<year> – single year, e.g. table:fact_sale:2022
    """
    local_root = cfg.local_data_root
    tasks: List[UploadTask] = []
    mode_lower = mode.lower()

    def _dim_tasks(table: str) -> List[UploadTask]:
        return [
            UploadTask(
                local_path=f,
                remote_path=f"full/{table}/{f.name}",
                table_name=table,
                load_type="full",
            )
            for f in sorted((local_root / "full" / table).glob("*.csv"))
        ]

    def _fact_tasks(filter_years: Optional[List[int]] = None) -> List[UploadTask]:
        result = []
        for f in sorted((local_root / "full" / FACT_SALE_FULL_DIR).glob("*.csv")):
            if filter_years:
                try:
                    yr = int(f.stem.split("_")[-1])
                    if yr not in filter_years:
                        continue
                except ValueError:
                    pass
            result.append(UploadTask(
                local_path=f,
                remote_path=f"full/{FACT_SALE_FULL_DIR}/{f.name}",
                table_name=FACT_SALE_FULL_DIR,
                load_type="full",
            ))
        return result

    def _incr_tasks() -> List[UploadTask]:
        return [
            UploadTask(
                local_path=f,
                remote_path=f"incremental/{INCREMENTAL_DIR}/{f.name}",
                table_name=INCREMENTAL_DIR,
                load_type="incremental",
            )
            for f in sorted(
                (local_root / "incremental" / INCREMENTAL_DIR).glob("*.csv")
            )
        ]

    if mode_lower == "full":
        for t in (tables or DIMENSION_TABLES):
            tasks.extend(_dim_tasks(t))
        tasks.extend(_fact_tasks(years))

    elif mode_lower == "incremental":
        tasks.extend(_incr_tasks())

    elif mode_lower == "dimensions":
        for t in (tables or DIMENSION_TABLES):
            tasks.extend(_dim_tasks(t))

    elif mode_lower == "fact":
        tasks.extend(_fact_tasks(years))

    elif mode_lower.startswith("table:"):
        parts = mode_lower.split(":")
        tname = parts[1]
        if tname == FACT_SALE_FULL_DIR:
            yr_filter = [int(parts[2])] if len(parts) == 3 else None
            tasks.extend(_fact_tasks(yr_filter))
        elif tname in (INCREMENTAL_DIR, "incremental"):
            tasks.extend(_incr_tasks())
        elif tname in DIMENSION_TABLES:
            tasks.extend(_dim_tasks(tname))
        else:
            raise ValueError(
                f"Unknown table '{tname}'. "
                f"Valid: {DIMENSION_TABLES + [FACT_SALE_FULL_DIR, INCREMENTAL_DIR]}"
            )
    else:
        raise ValueError(
            f"Unknown mode '{mode}'. "
            "Valid: full | incremental | dimensions | fact | table:<name>"
        )

    if not tasks:
        logger.warning("No files matched mode='%s' — nothing to upload.", mode)

    return tasks


# ─────────────────────────────────────────────────────────────────────────────
# Backend 1 — OneLake File Explorer  (local copy)
# ─────────────────────────────────────────────────────────────────────────────

class ExplorerUploader:
    """
    Copies files to OneLake via the locally-mounted File Explorer path.

    The OneLake Explorer syncs changes to the cloud transparently.
    No Azure SDK or credentials required.

    Destination layout:
      <onelake_explorer_root>/<workspace_folder>/<lakehouse_folder>/
          Files/pakmart/full/dimension_city/dimension_city.csv
          Files/pakmart/full/fact_sale/fact_sale_2022.csv
          Files/pakmart/incremental/fact_sale_1y_incremental/fact_sale_2023.csv
    """

    def __init__(self, cfg: PipelineConfig):
        self._cfg   = cfg
        self._root  = cfg.explorer_files_root   # already resolved in config
        self._root.mkdir(parents=True, exist_ok=True)
        logger.debug("Explorer destination root: %s", self._root)

    def _dest_path(self, task: UploadTask) -> Path:
        """Translate a relative remote_path to an absolute local destination."""
        # remote_path uses forward slashes; Path handles both on Windows
        return self._root / Path(task.remote_path)

    def _copy_one(self, task: UploadTask) -> UploadResult:
        dest = self._dest_path(task)

        # Skip-unchanged check: compare file sizes
        if self._cfg.skip_unchanged and dest.exists():
            if dest.stat().st_size == task.file_size_bytes:
                logger.debug("SKIP  %s (unchanged)", task.remote_path)
                return UploadResult(task=task, success=True, skipped=True)

        t0 = time.perf_counter()
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(task.local_path), str(dest))
            duration = time.perf_counter() - t0
            logger.info(
                "  ✓ %-58s  %6.2f MB  %5.1fs",
                task.remote_path,
                task.file_size_bytes / 1_048_576,
                duration,
            )
            return UploadResult(
                task=task,
                success=True,
                duration_sec=duration,
                bytes_uploaded=task.file_size_bytes,
            )
        except (OSError, IOError) as exc:
            logger.error("  ✗ %s  →  %s", task.remote_path, exc)
            return UploadResult(task=task, success=False, error=str(exc))

    def upload(self, tasks: List[UploadTask]) -> UploadReport:
        report = UploadReport(backend="explorer")
        if not tasks:
            print("  [explorer] No tasks.")
            return report

        total_mb = sum(t.file_size_bytes for t in tasks) / 1_048_576
        print(f"\n  Destination : {self._root}")
        print(f"  Files       : {len(tasks)}  ({total_mb:.2f} MB total)")
        print(f"  Workers     : {self._cfg.max_workers}\n")

        with ThreadPoolExecutor(max_workers=self._cfg.max_workers) as pool:
            futures = {pool.submit(self._copy_one, t): t for t in tasks}
            for future in as_completed(futures):
                report.results.append(future.result())

        return report


# ─────────────────────────────────────────────────────────────────────────────
# Backend 2 — Azure SDK (HTTPS / ADLS Gen2)
# ─────────────────────────────────────────────────────────────────────────────

class SDKUploader:
    """Uploads via the Azure Data Lake Storage Gen2 REST API."""

    def __init__(self, cfg: PipelineConfig, credential):
        from azure.storage.filedatalake import DataLakeServiceClient
        self._cfg = cfg
        self._svc = DataLakeServiceClient(
            account_url=cfg.dfs_account_url,
            credential=credential,
        )
        self._fs  = self._svc.get_file_system_client(cfg.filesystem_name)

    def _full_path(self, task: UploadTask) -> str:
        return f"{self._cfg.lakehouse_path_prefix}/{task.remote_path}"

    def _ensure_dir(self, dir_path: str):
        try:
            self._fs.get_directory_client(dir_path).create_directory()
        except Exception:
            pass

    def _remote_size(self, full_path: str) -> Optional[int]:
        try:
            return self._fs.get_file_client(full_path).get_file_properties().size
        except Exception:
            return None

    def _upload_one(self, task: UploadTask) -> UploadResult:
        from azure.core.exceptions import AzureError
        full_path = self._full_path(task)
        dir_path  = "/".join(full_path.split("/")[:-1])

        if self._cfg.skip_unchanged:
            if self._remote_size(full_path) == task.file_size_bytes:
                logger.debug("SKIP  %s (unchanged)", task.remote_path)
                return UploadResult(task=task, success=True, skipped=True)

        last_err: Optional[str] = None
        for attempt in range(1, self._cfg.max_retries + 1):
            t0 = time.perf_counter()
            try:
                self._ensure_dir(dir_path)
                with open(task.local_path, "rb") as fh:
                    self._fs.get_file_client(full_path).upload_data(
                        fh,
                        overwrite=True,
                        chunk_size=self._cfg.chunk_size,
                        max_concurrency=1,
                    )
                duration = time.perf_counter() - t0
                logger.info(
                    "  ✓ %-58s  %6.2f MB  %5.1fs",
                    task.remote_path,
                    task.file_size_bytes / 1_048_576,
                    duration,
                )
                return UploadResult(
                    task=task, success=True,
                    duration_sec=duration, bytes_uploaded=task.file_size_bytes,
                )
            except (AzureError, OSError, IOError) as exc:
                last_err = str(exc)
                wait = self._cfg.retry_backoff ** attempt
                logger.warning(
                    "  ✗ attempt %d/%d  %s: %s  (retry in %.0fs)",
                    attempt, self._cfg.max_retries, task.remote_path, last_err, wait,
                )
                if attempt < self._cfg.max_retries:
                    time.sleep(wait)

        return UploadResult(task=task, success=False, error=last_err)

    def upload(self, tasks: List[UploadTask]) -> UploadReport:
        report = UploadReport(backend="sdk")
        if not tasks:
            print("  [sdk] No tasks.")
            return report

        total_mb = sum(t.file_size_bytes for t in tasks) / 1_048_576
        print(f"\n  OneLake endpoint : {self._cfg.onelake_endpoint}")
        print(f"  Files            : {len(tasks)}  ({total_mb:.2f} MB total)")
        print(f"  Workers          : {self._cfg.max_workers}\n")

        with ThreadPoolExecutor(max_workers=self._cfg.max_workers) as pool:
            futures = {pool.submit(self._upload_one, t): t for t in tasks}
            for future in as_completed(futures):
                report.results.append(future.result())

        return report
