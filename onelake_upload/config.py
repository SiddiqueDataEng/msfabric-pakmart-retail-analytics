"""
config.py – Pipeline settings.

Two upload backends are supported, auto-detected by priority:

  1. explorer  – OneLake File Explorer is mounted locally (e.g.
                 C:\\Users\\Admin\\OneLake - Microsoft\\My workspace).
                 Zero credentials required. Just a file copy.

  2. sdk       – Azure Data Lake Storage Gen2 SDK over HTTPS.
                 Requires service-principal / device-code / CLI auth.

Set UPLOAD_BACKEND=explorer or UPLOAD_BACKEND=sdk in .env (or leave it
blank and the pipeline will auto-detect: if the explorer mount exists it
wins, otherwise it falls back to sdk).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    for _candidate in (
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ):
        if _candidate.exists():
            load_dotenv(_candidate)
            break
except ImportError:
    pass


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Copy .env.template to .env and fill in your values."
        )
    return val


# ── OneLake Explorer default root (Windows) ───────────────────────────────────
_EXPLORER_DEFAULT = Path(os.environ.get("USERPROFILE", "C:/Users/Admin")) / "OneLake - Microsoft"


@dataclass
class PipelineConfig:

    # ── Backend selection ─────────────────────────────────────────────────────
    # "explorer" | "sdk" | "auto"  (auto = explorer if mount exists, else sdk)
    upload_backend: str = field(
        default_factory=lambda: os.getenv("UPLOAD_BACKEND", "auto").lower()
    )

    # ── OneLake Explorer settings (backend=explorer) ──────────────────────────
    # Root of the OneLake Explorer mount, e.g.
    #   C:\Users\Admin\OneLake - Microsoft
    onelake_explorer_root: Path = field(
        default_factory=lambda: Path(
            os.getenv("ONELAKE_EXPLORER_ROOT", str(_EXPLORER_DEFAULT))
        )
    )
    # Name of the Fabric workspace folder inside the explorer root
    # e.g. "My workspace"  →  full path becomes:
    #   C:\Users\Admin\OneLake - Microsoft\My workspace\<lakehouse>\Files\pakmart
    workspace_folder: str = field(
        default_factory=lambda: os.getenv("WORKSPACE_FOLDER", "My workspace")
    )
    # Name of the Lakehouse item folder, e.g. "freeway_data.Lakehouse"
    lakehouse_folder: str = field(
        default_factory=lambda: os.getenv("LAKEHOUSE_FOLDER", "")
    )

    # ── SDK / HTTPS settings (backend=sdk) ────────────────────────────────────
    auth_method: str = field(
        default_factory=lambda: os.getenv("AUTH_METHOD", "service_principal")
    )
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    workspace_id: str = ""
    lakehouse_id: str = ""
    onelake_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "ONELAKE_ENDPOINT", "https://onelake.dfs.fabric.microsoft.com"
        )
    )

    # ── Local source data ─────────────────────────────────────────────────────
    local_data_root: Path = field(
        default_factory=lambda: Path(os.getenv("LOCAL_DATA_ROOT", "../pakmart_data"))
    )

    # ── Upload behaviour ──────────────────────────────────────────────────────
    max_workers: int = field(
        default_factory=lambda: int(os.getenv("MAX_WORKERS", "6"))
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "4194304"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRIES", "3"))
    )
    retry_backoff: float = field(
        default_factory=lambda: float(os.getenv("RETRY_BACKOFF", "2"))
    )
    skip_unchanged: bool = field(
        default_factory=lambda: os.getenv("SKIP_UNCHANGED", "True").lower() == "true"
    )

    # Remote sub-path inside the lakehouse Files folder
    remote_files_subdir: str = field(
        default_factory=lambda: os.getenv("REMOTE_FILES_SUBDIR", "pakmart")
    )

    # Internal — skip credential validation for dry-run
    _skip_validation: bool = field(default=False, repr=False)

    # ── Post-init ─────────────────────────────────────────────────────────────

    def __post_init__(self):
        self.local_data_root      = Path(self.local_data_root)
        self.onelake_explorer_root = Path(self.onelake_explorer_root)

        # Resolve "auto" backend
        if self.upload_backend == "auto":
            self.upload_backend = (
                "explorer" if self._explorer_mount_exists() else "sdk"
            )

        if self._skip_validation:
            return

        if self.upload_backend == "explorer":
            self._validate_explorer()
        else:
            self._validate_sdk()

    # ── Explorer validation ───────────────────────────────────────────────────

    def _explorer_mount_exists(self) -> bool:
        return (
            self.onelake_explorer_root.exists()
            and any(self.onelake_explorer_root.iterdir())
        )

    def _validate_explorer(self):
        if not self.onelake_explorer_root.exists():
            raise EnvironmentError(
                f"OneLake Explorer root not found: {self.onelake_explorer_root}\n"
                "Install OneLake File Explorer from "
                "https://www.microsoft.com/store/productId/9NQZL0ZMB919\n"
                "or set ONELAKE_EXPLORER_ROOT in .env."
            )

        # List all synced workspace folders for helpful error messages
        all_workspaces = [
            p.name for p in self.onelake_explorer_root.iterdir() if p.is_dir()
        ]

        ws_path = self.onelake_explorer_root / self.workspace_folder
        if not ws_path.exists():
            raise EnvironmentError(
                f"\n  Workspace folder '{self.workspace_folder}' is NOT synced in OneLake Explorer.\n\n"
                f"  Currently synced workspaces: {all_workspaces}\n\n"
                "  To fix:\n"
                "    1. Click the OneLake icon in the Windows system tray\n"
                "    2. Click 'Add a workspace'\n"
                f"   3. Select '{self.workspace_folder}' and click Sync\n"
                f"   4. Wait for  {self.onelake_explorer_root / self.workspace_folder}  to appear\n"
                "    5. Re-run this command\n\n"
                "  Or set WORKSPACE_FOLDER in .env to one of the already-synced workspaces:\n"
                f"   {all_workspaces}"
            )

        # Auto-detect lakehouse if not specified
        if not self.lakehouse_folder:
            lakehouses = [
                p.name for p in ws_path.iterdir()
                if p.is_dir() and p.name.endswith(".Lakehouse")
            ]
            if not lakehouses:
                raise EnvironmentError(
                    f"No Lakehouse found inside workspace '{self.workspace_folder}'.\n"
                    "Create a Lakehouse in Fabric first, then re-run.\n"
                    f"Path checked: {ws_path}"
                )
            self.lakehouse_folder = lakehouses[0]
            print(f"[config] Auto-detected lakehouse: {self.lakehouse_folder}")

        lh_path = ws_path / self.lakehouse_folder
        if not lh_path.exists():
            available = [p.name for p in ws_path.iterdir() if p.is_dir()]
            raise EnvironmentError(
                f"Lakehouse '{self.lakehouse_folder}' not found under {ws_path}.\n"
                f"Available items: {available}"
            )

    # ── SDK validation ────────────────────────────────────────────────────────

    def _validate_sdk(self):
        if self.auth_method == "service_principal":
            self.tenant_id     = _require("AZURE_TENANT_ID")
            self.client_id     = _require("AZURE_CLIENT_ID")
            self.client_secret = _require("AZURE_CLIENT_SECRET")
        self.workspace_id = _require("FABRIC_WORKSPACE_ID")
        self.lakehouse_id = _require("FABRIC_LAKEHOUSE_ID")

    # ── Derived paths (explorer backend) ─────────────────────────────────────

    @property
    def explorer_files_root(self) -> Path:
        """
        The local path that maps to  <lakehouse>/Files/pakmart/
        e.g.  C:\\Users\\Admin\\OneLake - Microsoft\\My workspace
                  \\freeway_data.Lakehouse\\Files\\pakmart
        """
        return (
            self.onelake_explorer_root
            / self.workspace_folder
            / self.lakehouse_folder
            / "Files"
            / self.remote_files_subdir
        )

    # ── Derived paths (SDK backend) ───────────────────────────────────────────

    @property
    def dfs_account_url(self) -> str:
        return self.onelake_endpoint

    @property
    def filesystem_name(self) -> str:
        return self.workspace_id

    @property
    def lakehouse_path_prefix(self) -> str:
        return f"{self.lakehouse_id}/Files/{self.remote_files_subdir}"
