# PakMart → OneLake Upload Pipeline

Uploads the generated Pakistani retail data (`pakmart_data/`) to Microsoft Fabric OneLake automatically, supporting full load, incremental load, partial/selective loads, and scheduled execution.

---

## Architecture

```
pakmart_data/
├── full/
│   ├── dimension_city/          ← 1 CSV
│   ├── dimension_customer/      ← 1 CSV
│   ├── dimension_date/          ← 1 CSV
│   ├── dimension_employee/      ← 1 CSV
│   ├── dimension_stock_item/    ← 1 CSV
│   └── fact_sale/               ← 4 CSVs (one per year)
└── incremental/
    └── fact_sale_1y_incremental/ ← 1 CSV (2023)
```

Files are uploaded to OneLake at:
```
<workspace_id>/<lakehouse_id>/Files/pakmart/<full|incremental>/...
```

The Fabric Bronze→Silver notebook reads from `Files/pakmart/full/` and `Files/pakmart/incremental/`.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.template .env
# Edit .env and fill in your values
```

Required values in `.env`:

| Variable | Description |
|---|---|
| `AUTH_METHOD` | `service_principal` / `device_code` / `cli` |
| `AZURE_TENANT_ID` | Your Azure AD tenant GUID |
| `AZURE_CLIENT_ID` | Service principal app (client) ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `FABRIC_WORKSPACE_ID` | Fabric workspace GUID (Settings → Workspace info) |
| `FABRIC_LAKEHOUSE_ID` | Lakehouse GUID (right-click lakehouse → Properties) |

> **Tip — finding the Lakehouse ID:** In Fabric, open the lakehouse → look at the URL:  
> `https://app.fabric.microsoft.com/groups/<workspace_id>/lakehouses/<lakehouse_id>`

---

## Usage

### Quick-start batch scripts (Windows)

| Script | What it does |
|---|---|
| `run_dry_run.bat` | Preview what would be uploaded (no credentials needed) |
| `run_full_load.bat` | Upload everything — all dimensions + all fact years |
| `run_incremental.bat` | Upload only the 2023 incremental file |
| `run_partial_load.bat` | Edit variables inside the file to upload a subset |

### CLI (`main.py`)

```bash
# Full load
python main.py --mode full

# Full load, specific tables only
python main.py --mode full --tables dimension_city dimension_stock_item

# Full load, specific years only
python main.py --mode full --years 2021 2022

# Incremental load (2023)
python main.py --mode incremental

# Dimensions only (master data refresh)
python main.py --mode dimensions

# Fact tables only
python main.py --mode fact

# Fact table for one year
python main.py --mode fact --years 2022

# Single table
python main.py --mode table:dimension_stock_item
python main.py --mode table:fact_sale:2022

# Dry run — see the file list, no upload
python main.py --mode full --dry-run

# Force overwrite (ignore skip_unchanged)
python main.py --mode incremental --force

# Override workers and data root
python main.py --mode full --workers 8 --data-root C:\data\pakmart_data

# Verbose output
python main.py --mode full --log-level DEBUG
```

### Python API

```python
from onelake_upload.pipeline import run_pipeline
from onelake_upload.config import PipelineConfig

cfg = PipelineConfig()   # reads from environment / .env

# Full load
report = run_pipeline(mode="full", cfg=cfg)

# Incremental
report = run_pipeline(mode="incremental", cfg=cfg)

# Partial: two dimension tables only
report = run_pipeline(
    mode="dimensions",
    tables=["dimension_city", "dimension_stock_item"],
    cfg=cfg,
)

# Partial: fact 2022 only
report = run_pipeline(mode="fact", years=[2022], cfg=cfg)

# Inspect results
print(f"Uploaded: {report.succeeded}, Skipped: {report.skipped}, Failed: {report.failed}")
```

---

## Load Modes Reference

| Mode | Tables affected | Typical use |
|---|---|---|
| `full` | All dimensions + all fact years | Initial load, weekly refresh |
| `incremental` | `fact_sale_1y_incremental` only | Daily append |
| `dimensions` | All 5 dimension tables | Master data refresh |
| `fact` | All fact year files (optionally filtered by `--years`) | Backfill / partial reload |
| `table:<name>` | One specific table | Targeted fix/reupload |
| `table:fact_sale:<year>` | One year of fact_sale | Single-year reupload |

---

## Scheduling (Windows)

Run `schedule_tasks.ps1` once from an elevated PowerShell prompt to register three Windows Scheduled Tasks:

| Task name | Trigger | Mode |
|---|---|---|
| `PakMart-FullLoad` | Every Sunday 01:00 | `full` |
| `PakMart-Incremental` | Daily 02:00 | `incremental` |
| `PakMart-DimensionsOnly` | Every 6 hours | `dimensions` |

```powershell
# Register tasks
.\schedule_tasks.ps1

# Test immediately
Start-ScheduledTask -TaskName "PakMart-FullLoad"

# View status
Get-ScheduledTask -TaskName "PakMart-*" | Select TaskName, State

# Remove all
Get-ScheduledTask -TaskName "PakMart-*" | Unregister-ScheduledTask -Confirm:$false
```

Logs are written to `onelake_upload/logs/`.

---

## How idempotency works

When `SKIP_UNCHANGED=True` (the default), before uploading a file the pipeline calls `get_file_properties()` on the remote path. If the remote file's byte size matches the local file's byte size, the upload is skipped. This makes repeated runs safe — only genuinely changed files are re-transmitted.

Use `--force` (or `SKIP_UNCHANGED=False`) to always overwrite.

---

## Auth methods

| Method | When to use |
|---|---|
| `service_principal` | CI/CD, scheduled tasks, automation — recommended |
| `device_code` | Interactive developer login (browser popup) |
| `cli` | Local dev where `az login` is already done |

---

## File layout after upload

```
OneLake
└── <workspace_id>/
    └── <lakehouse_id>/
        └── Files/
            └── pakmart/
                ├── full/
                │   ├── dimension_city/dimension_city.csv
                │   ├── dimension_customer/dimension_customer.csv
                │   ├── dimension_date/dimension_date.csv
                │   ├── dimension_employee/dimension_employee.csv
                │   ├── dimension_stock_item/dimension_stock_item.csv
                │   └── fact_sale/
                │       ├── fact_sale_2019.csv
                │       ├── fact_sale_2020.csv
                │       ├── fact_sale_2021.csv
                │       └── fact_sale_2022.csv
                └── incremental/
                    └── fact_sale_1y_incremental/
                        └── fact_sale_2023.csv
```

This matches exactly the paths the Bronze→Silver Fabric notebook reads from.
