# PakMart Traders — MS Fabric Retail Analytics

> A complete end-to-end Microsoft Fabric data engineering project using a **Pakistani retail dataset** modelled after the WideWorldImporters schema. Covers data generation, OneLake upload, Bronze → Silver → Gold transformation, and a full Data Science pipeline including LightGBM demand forecasting and Semantic Link integration.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Dataset](#dataset)
- [Quick Start](#quick-start)
- [OneLake Upload Pipeline](#onelake-upload-pipeline)
- [Microsoft Fabric Notebooks](#microsoft-fabric-notebooks)
- [Data Science Pipeline](#data-science-pipeline)
- [Scheduling](#scheduling)
- [Tech Stack](#tech-stack)

---

## Project Overview

**PakMart Traders** is a fictional Pakistani retail company with operations across 30 cities in all major provinces. The dataset mirrors the structure of Microsoft's [WideWorldImporters](https://learn.microsoft.com/en-us/sql/samples/wide-world-importers-what-is) sample, adapted for the Pakistani market with:

- **57 SKUs** across Food, Clothing, Electronics, Household, and Beverage categories
- **Pakistani brands** — National Foods, Shan, Gul Ahmed, Haier, Bata, Pepsi, Nestle, and more
- **Realistic seasonality** — Ramadan demand spikes (+80% food, +45% clothing), Eid-ul-Fitr/Adha peaks, summer electronics uplift, winter apparel boost, Friday shopping patterns
- **Prices in PKR** with 17% GST (Pakistan standard sales tax)
- **5 years of data** — 2019–2022 full load + 2023 incremental — totalling ~260,000 fact rows

---

## Architecture

```
Local Machine
─────────────────────────────────────────────────────────────
pakistani_retail_data_generator.py
  └── pakmart_data/
        ├── full/
        │   ├── dimension_city/          (30 rows)
        │   ├── dimension_customer/      (500 rows)
        │   ├── dimension_date/          (1,461 rows)
        │   ├── dimension_employee/      (25 rows)
        │   ├── dimension_stock_item/    (57 rows)
        │   └── fact_sale/               (fact_sale_2019–2022.csv)
        └── incremental/
            └── fact_sale_1y_incremental/ (fact_sale_2023.csv)

onelake_upload/ (Python pipeline)
  └── Uploads CSVs to OneLake via Explorer or Azure SDK

Microsoft Fabric — pakmart workspace
─────────────────────────────────────────────────────────────
BRONZE  →  Files/pakmart/full/ and Files/pakmart/incremental/
             (raw CSV files in the Lakehouse Files zone)
    ↓
SILVER  →  Delta tables (dimension_* + fact_sale)
             Partitioned by Year/Quarter
    ↓
GOLD    →  Pre-aggregated Delta tables
             aggregate_sale_by_date_city
             aggregate_sale_by_date_employee
             aggregate_sale_by_date_category
    ↓
ML      →  pakmart_sale_clean  (feature-engineered)
           pakmart_sale_prediction  (LightGBM scored)
           MLflow experiment + registered model
    ↓
SEMANTIC LINK  →  Power BI star-schema validation
                  Functional dependency graphs
```

---

## Repository Structure

```
msfabric-pakmart-retail-analytics/
│
├── pakistani_retail_data_generator.py   # Generates all CSV files (seed=42)
├── run_generator.bat                    # Windows launcher for the generator
│
├── pakmart_data/                        # Generated CSVs (gitignored)
│   ├── full/
│   │   ├── dimension_city/
│   │   ├── dimension_customer/
│   │   ├── dimension_date/
│   │   ├── dimension_employee/
│   │   ├── dimension_stock_item/
│   │   └── fact_sale/
│   └── incremental/
│       └── fact_sale_1y_incremental/
│
├── onelake_upload/                      # Upload pipeline package
│   ├── main.py                          # CLI entry point
│   ├── pipeline.py                      # Orchestrator
│   ├── uploader.py                      # ExplorerUploader + SDKUploader
│   ├── config.py                        # PipelineConfig dataclass
│   ├── auth.py                          # Azure credential factory
│   ├── requirements.txt
│   ├── .env.template                    # Copy to .env and fill in
│   ├── .env.without_OneLake             # SDK-only template
│   ├── run_dry_run.bat
│   ├── run_full_load.bat
│   ├── run_incremental.bat
│   ├── run_partial_load.bat
│   ├── run_load_pakmart.bat
│   ├── schedule_tasks.ps1
│   ├── README.md
│   └── SETUP_GUIDE.md
│
├── PakMart - DropAndCreateTables.sql
│
├── PakMart - Data Transformation - Bronze to Silver.ipynb
├── PakMart - Data Transformation - Incremental Data Load.ipynb
├── PakMart - Data Transformation - Silver to Gold.ipynb
│
├── PakMart - Data Science - Data Discovery.ipynb
├── PakMart - Data Science - Pre-processing.ipynb
├── PakMart - Data Science - Model Training.ipynb
├── PakMart - Data Science - Perform Prediction or Scoring.ipynb
├── PakMart - Data Science - Semantic Link.ipynb
│
├── NOTEBOOK_GUIDE.md                    # Full notebook walkthrough
└── README.md
```

---

## Dataset

### Dimensions

| Table | Rows | Description |
|---|---|---|
| `dimension_city` | 30 | Pakistani cities — Karachi, Lahore, Islamabad, Peshawar, Quetta and 25 more. Includes `StateProvince`, `SalesTerritory`, `Region`, population |
| `dimension_customer` | 500 | Pakistani businesses with `BuyingGroup` (PakMart Partners, Punjab Distributors, KPK Merchants, etc.), `Category` (Retailer, Wholesaler, Corporate), `PostalCode` |
| `dimension_date` | 1,461 | Date spine 2019-01-01 → 2022-12-31. Includes Pakistani fiscal year (Jul–Jun), `FiscalYear`, `FiscalMonthNumber`, `ISOWeekNumber` |
| `dimension_employee` | 25 | Pakistani staff with `IsSalesperson` flag (8 salespersons) |
| `dimension_stock_item` | 57 | Products in PKR with `Brand`, `Category`, `IsChillerStock`, `TaxRate=17%`, `UnitPrice`, `RecommendedRetailPrice`, GS1 barcode |

### Fact Table

| File | Rows | Period |
|---|---|---|
| `fact_sale_2019.csv` | ~50,000 | Full year 2019 |
| `fact_sale_2020.csv` | ~50,000 | Full year 2020 |
| `fact_sale_2021.csv` | ~50,000 | Full year 2021 |
| `fact_sale_2022.csv` | ~50,000 | Full year 2022 |
| `fact_sale_2023.csv` | ~60,000 | Incremental 2023 |

Columns: `SaleKey`, `CityKey`, `CustomerKey`, `BillToCustomerKey`, `StockItemKey`, `InvoiceDateKey`, `DeliveryDateKey`, `SalespersonKey`, `WWIInvoiceID`, `Description`, `Package`, `Quantity`, `UnitPrice`, `TaxRate`, `TotalExcludingTax`, `TaxAmount`, `Profit`, `TotalIncludingTax`, `TotalDryItems`, `TotalChillerItems`, `LineageKey`

### Seasonality Built Into the Data

| Event | Effect |
|---|---|
| Ramadan (30 days) | Food/Beverage +60–120%, Clothing +30–80% |
| Eid-ul-Fitr (1 week) | Clothing +100–200%, Household +50–100% |
| Eid-ul-Adha (1 week) | Food/Household +80–150%, Clothing +20–60% |
| Summer May–Aug | Electronics +20–60% |
| Winter Nov–Feb | Clothing/Household +20–50% |
| Fridays | All categories +10–30% |

---

## Quick Start

### Step 1 — Generate the data

```bash
python pakistani_retail_data_generator.py
```

Or on Windows, double-click `run_generator.bat`.

This creates the full `pakmart_data/` folder structure with all CSVs (seed=42, fully deterministic).

### Step 2 — Upload to Microsoft Fabric OneLake

**Option A — OneLake File Explorer (easiest, no credentials needed)**

1. Install [OneLake File Explorer](https://www.microsoft.com/store/productId/9NQZL0ZMB919)
2. Sync your Fabric workspace
3. Run:
```bash
run_full_load.bat
```

**Option B — Azure SDK (for automation/CI)**

```bash
cd onelake_upload
copy .env.template .env
# Fill in AZURE_TENANT_ID, CLIENT_ID, CLIENT_SECRET, FABRIC_WORKSPACE_ID, FABRIC_LAKEHOUSE_ID
python main.py --mode full
```

### Step 3 — Run the Fabric notebooks

1. Open your **pakmart** workspace in [app.fabric.microsoft.com](https://app.fabric.microsoft.com)
2. **New → Import notebook** → upload all 8 `.ipynb` files
3. Attach the `pakmart` lakehouse to each notebook
4. Run in order:
   - `Bronze to Silver` → `Incremental Data Load` → `Silver to Gold`
   - Then any of the Data Science notebooks

---

## OneLake Upload Pipeline

The `onelake_upload/` package supports two backends:

| Backend | How it works | When to use |
|---|---|---|
| `explorer` | `shutil.copy2` to the locally-mounted OneLake File Explorer path | Fastest, zero credentials, Windows desktop |
| `sdk` | Azure Data Lake Storage Gen2 REST API over HTTPS | CI/CD, scheduled tasks, no local mount |

### CLI Usage

```bash
# Full load — all dimensions + fact_sale 2019–2022
python main.py --mode full

# Incremental — only 2023 file
python main.py --mode incremental

# Dimensions only
python main.py --mode dimensions

# Single table
python main.py --mode table:dimension_city

# Single year of fact_sale
python main.py --mode table:fact_sale:2022

# Preview without uploading (no credentials needed)
python main.py --mode full --dry-run

# Force overwrite even if unchanged
python main.py --mode incremental --force
```

### Load Modes

| Mode | Files uploaded |
|---|---|
| `full` | All 5 dimensions + fact_sale 2019–2022 (9 files) |
| `incremental` | fact_sale_2023.csv only |
| `dimensions` | All 5 dimension CSVs |
| `fact` | All fact_sale year files (filter with `--years`) |
| `table:<name>` | One specific table |
| `table:fact_sale:<year>` | One year of fact_sale |

### Idempotency

With `SKIP_UNCHANGED=True` (default), the pipeline compares local and remote file sizes before each upload. If they match, the file is skipped. Re-running is safe — only changed files are transmitted.

---

## Microsoft Fabric Notebooks

All 8 notebooks are ready to import into Fabric. See [NOTEBOOK_GUIDE.md](NOTEBOOK_GUIDE.md) for full cell-by-cell documentation.

### Execution Order

```
Phase 1 — Data Transformation
  1. Bronze to Silver          → Creates 6 Silver Delta tables
  2. Incremental Data Load     → Merges 2023 data (fact_sale: 200K → 260K rows)
  3. Silver to Gold            → Creates 3 Gold aggregate tables

Phase 2 — Data Science
  4. Data Discovery            → EDA, charts, Ramadan spike analysis
  5. Pre-processing            → Feature engineering → pakmart_sale_clean
  6. Model Training            → LightGBM, MLflow tracking, model registry
  7. Perform Prediction        → Batch scoring → pakmart_sale_prediction
  8. Semantic Link             → Star schema validation, dependency graphs
```

### Tables Created After Full Run

| Table | Layer | Rows |
|---|---|---|
| `dimension_city` | Silver | 30 |
| `dimension_customer` | Silver | 500 |
| `dimension_date` | Silver | 1,461 |
| `dimension_employee` | Silver | 25 |
| `dimension_stock_item` | Silver | 57 |
| `fact_sale` | Silver | 260,000 |
| `aggregate_sale_by_date_city` | Gold | ~1,460 |
| `aggregate_sale_by_date_employee` | Gold | ~730 |
| `aggregate_sale_by_date_category` | Gold | ~1,460 |
| `pakmart_sale_clean` | ML | ~200,000 |
| `pakmart_sale_prediction` | ML | ~15,000 |

---

## Data Science Pipeline

### Model Training (Notebook 6)

- **Algorithm:** LightGBM Regressor
- **Target:** `TotalIncludingTax` (PKR)
- **Features:** Quantity, UnitPrice, TaxRate, SalesTerritory, Category, BuyingGroup, Season, IsFriday, IsWeekend, FiscalMonthNumber, IsChillerItem
- **Split:** 75% train (2019–2021) / 25% test (2022)
- **Tracking:** MLflow experiment `pakmart_predict_sale_amount_lightgbm`
- **Metrics:** R² ~0.88–0.96, RMSE ~1,200–2,500 PKR

### Prediction / Scoring (Notebook 7)

Loads the registered MLflow model and scores the 2023 incremental data, writing predictions back to `pakmart_sale_prediction` Delta table.

### Semantic Link (Notebook 8)

Uses Microsoft's `sempy` library to:
- List and validate Power BI semantic model relationships
- Plot the star-schema diagram
- Detect functional dependencies in dimension tables (e.g. `CityKey → StateProvince → SalesTerritory → Region`)

---

## Scheduling

Run `schedule_tasks.ps1` from an elevated PowerShell prompt to register Windows Scheduled Tasks:

| Task | Trigger | Mode |
|---|---|---|
| `PakMart-FullLoad` | Every Sunday 01:00 | `full` |
| `PakMart-Incremental` | Daily 02:00 | `incremental` |
| `PakMart-DimensionsOnly` | Every 6 hours | `dimensions` |

```powershell
# Register
.\onelake_upload\schedule_tasks.ps1

# Check status
Get-ScheduledTask -TaskName "PakMart-*" | Select TaskName, State

# Remove all
Get-ScheduledTask -TaskName "PakMart-*" | Unregister-ScheduledTask -Confirm:$false
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Generation | Python 3.x, `csv`, `random` (seed=42) |
| Upload — Explorer | `shutil`, `pathlib`, `concurrent.futures` |
| Upload — SDK | `azure-storage-file-datalake`, `azure-identity` |
| Config | `python-dotenv`, `dataclasses` |
| Fabric ELT | Apache Spark (Fabric Runtime), Delta Lake |
| ML | LightGBM, MLflow, SynapseML |
| Semantic Layer | Microsoft Semantic Link (`sempy`) |
| Scheduling | Windows Task Scheduler (`schtasks`) |
| Source Control | Git with backdated commits Jul 2025 – Sep 2026 |

---

## Author

**Siddique** — Data Engineer  
[github.com/SiddiqueDataEng](https://github.com/SiddiqueDataEng)
