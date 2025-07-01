# PakMart Traders — Notebook Execution Guide

Complete walkthrough of all 8 notebooks in run order, with purpose, step-by-step cell explanations, expected outcomes, and upload instructions.

---

## Architecture overview

```
Local machine                   Microsoft Fabric — pakmart workspace
─────────────────               ──────────────────────────────────────────────────────
pakistani_retail_              ┌─ BRONZE ──────────────────────────────────────────┐
data_generator.py  ──copy──►  │  <lakehouse>/Files/pakmart/full/                   │
(262,074 rows)      Explorer  │    dimension_city / customer / date /              │
                              │    employee / stock_item / fact_sale (×4 years)    │
                              │  <lakehouse>/Files/pakmart/incremental/             │
                              │    fact_sale_1y_incremental (2023)                 │
                              └────────────────┬──────────────────────────────────┘
                                               │ Notebook 1: Bronze → Silver
                                               ▼
                              ┌─ SILVER ──────────────────────────────────────────┐
                              │  Delta tables: dimension_* + fact_sale             │
                              │  Partitioned by Year / Quarter                     │
                              └────────────────┬──────────────────────────────────┘
                                               │ Notebook 2: Incremental Load
                                               │ Notebook 3: Silver → Gold
                                               ▼
                              ┌─ GOLD ────────────────────────────────────────────┐
                              │  aggregate_sale_by_date_city                       │
                              │  aggregate_sale_by_date_employee                   │
                              │  aggregate_sale_by_date_category                   │
                              └────────────────┬──────────────────────────────────┘
                                               │ Notebooks 4-8: Data Science
                                               ▼
                              ┌─ ML / ANALYTICS ──────────────────────────────────┐
                              │  pakmart_sale_clean (feature-engineered)           │
                              │  pakmart_sale_prediction (scored)                  │
                              │  MLflow experiment + registered model              │
                              │  Semantic Link relationship graph                  │
                              └───────────────────────────────────────────────────┘
```

---

## Before you run any notebook

### One-time setup in Fabric

1. Open [app.fabric.microsoft.com](https://app.fabric.microsoft.com) → **pakmart** workspace
2. Create a Lakehouse named **`pakmart`** (New → Lakehouse → `pakmart`)
3. When the lakehouse opens, **attach it as the default lakehouse** in every notebook (top-left of the notebook editor → "Add lakehouse" → select `pakmart`)
4. Upload the CSV files via OneLake Explorer (sync the pakmart workspace, then run `run_load_pakmart.bat`)

### How to upload the notebooks themselves

Yes — you can upload the `.ipynb` files directly from your local machine to Fabric:

1. In the **pakmart** workspace, click **New → Import notebook**
2. Click **Upload** → select all 8 `PakMart - *.ipynb` files from `f:\siddi\msfabric_retails_data\`
3. They appear in the workspace immediately, ready to run
4. Open each one → **Add lakehouse** (top-left) → select `pakmart` → **Add**

> The `.ipynb` files are already in `f:\siddi\msfabric_retails_data\` — you do **not** need to re-create them in Fabric.

---

## Run order

```
Phase 1 — Data Transformation (ELT)
  [1]  Bronze to Silver
  [2]  Incremental Data Load        ← run after [1]
  [3]  Silver to Gold               ← run after [1]

Phase 2 — Data Science
  [4]  Data Discovery               ← run after [1]
  [5]  Pre-processing               ← run after [1]
  [6]  Model Training               ← run after [5]
  [7]  Perform Prediction/Scoring   ← run after [6]
  [8]  Semantic Link                ← run after [3]
```

---

## Notebook 1 — Bronze to Silver

**File:** `PakMart - Data Transformation - Bronze to Silver.ipynb`

### Why it exists

Raw CSV files sitting in the `Files/` zone are just bytes — no schema enforcement, no compression, no query optimisation. This notebook is the **ingestion layer**. It reads every CSV with an explicit schema (which prevents Spark from guessing wrong types), converts each file to **Delta Lake format**, and writes it into the `Tables/` section of the lakehouse where it becomes a proper queryable table.

### What each cell does

| Cell | What it does |
|---|---|
| dimension_city | Reads `Files/pakmart/full/dimension_city/*.csv` with typed schema (CityKey INT, Population BIGINT, ValidFrom TIMESTAMP, etc.) → writes Delta table `dimension_city` |
| dimension_customer | Same pattern → `dimension_customer` Delta table (500 Pakistani business customers) |
| dimension_date | Reads the date spine (2019-01-01 → 2022-12-31, 1,461 rows) with Pakistani fiscal year columns → `dimension_date` |
| dimension_employee | 25 Pakistani employees, IsSalesperson flag → `dimension_employee` |
| dimension_stock_item | 58 products (Food, Clothing, Electronics, Household, Beverages) with PKR pricing → `dimension_stock_item` |
| fact_sale | Reads all 4 year-partitioned CSVs at once (200,000 rows), derives `Year`, `Quarter`, `Month` columns, **partitions the Delta table by Year and Quarter** for fast time-range queries → `fact_sale` |
| Verification SQL | `SELECT Year, Quarter, Month, count(*) FROM fact_sale GROUP BY ...` — row count check per partition |

### Expected outcome

After running, the lakehouse **Tables** section shows 6 Delta tables:

```
Tables/
  dimension_city          30 rows
  dimension_customer     500 rows
  dimension_date       1,461 rows
  dimension_employee      25 rows
  dimension_stock_item    58 rows
  fact_sale          200,000 rows   (partitioned by Year/Quarter)
```

The SQL verification cell returns:

| Year | Quarter | Month | count |
|---|---|---|---|
| 2019 | 1 | 1 | ~4,200 |
| ... | ... | ... | ... |
| 2022 | 4 | 12 | ~4,200 |

---

## Notebook 2 — Incremental Data Load

**File:** `PakMart - Data Transformation - Incremental Data Load.ipynb`

> Run after Notebook 1.

### Why it exists

In production, new sales arrive daily. You can't overwrite the entire `fact_sale` table every night — it's too slow and loses history. This notebook demonstrates **Delta Lake MERGE** (the SQL `UPSERT` pattern): new rows get inserted, existing rows get updated if they were corrected. Partition pruning (`Year IN (2023)`) makes it only touch the 2023 partitions, not the 2019–2022 data.

### What each cell does

| Cell | What it does |
|---|---|
| Read incremental CSV | Loads `Files/pakmart/incremental/fact_sale_1y_incremental/fact_sale_2023.csv` (60,000 rows) → adds `Year`, `Quarter`, `Month` columns → creates a Spark temporary view `fact_sale_incremental` |
| Count verification | Shows rows per month in 2023 — confirms the data was read correctly |
| DELTA MERGE | Runs MERGE INTO `fact_sale` targeting only `Year=2023` partitions. **MATCHED** = update all columns. **NOT MATCHED** = insert new row |
| Post-merge count | Same GROUP BY query — now shows 2019–2023 in the result |
| DESCRIBE HISTORY | Shows the Delta transaction log — version 0 = initial load, version 1 = merge operation |

### Expected outcome

`fact_sale` grows from 200,000 to **260,000 rows**. `DESCRIBE HISTORY` shows:

```
version | operation  | operationParameters
--------|------------|--------------------
1       | MERGE      | {"predicate": "...Year IN (2023)..."}
0       | WRITE      | {"mode": "Overwrite"}
```

---

## Notebook 3 — Silver to Gold

**File:** `PakMart - Data Transformation - Silver to Gold.ipynb`

> Run after Notebook 1 (and optionally after Notebook 2 to include 2023).

### Why it exists

Power BI reports and dashboards need **pre-aggregated, denormalised** data to render quickly. Joining 5 tables at query time on 260,000+ rows every time a report refreshes is wasteful. Gold tables do the heavy joins and aggregations once, storing the results as Delta tables that Power BI reads directly.

### What each cell does

| Cell | What it does |
|---|---|
| Load Silver tables | Reads `fact_sale`, `dimension_date`, `dimension_city` from the silver layer |
| **Aggregate 1** — sale_by_date_city | Joins fact + date + city → groups by Date / CalendarYear / FiscalYear / Province / SalesTerritory → sums TotalExcludingTax, TaxAmount, TotalIncludingTax, Profit → writes `Tables/aggregate_sale_by_date_city` |
| **Aggregate 2** — sale_by_date_employee | SQL: joins fact + date + employee → groups by Date / FiscalYear / Salesperson → sums revenue and profit → writes `Tables/aggregate_sale_by_date_employee` |
| **Aggregate 3** — sale_by_date_category | SQL: joins fact + date + city → groups by Date / FiscalYear / City / Province / Territory → sums revenue, profit, dry items, chiller items → writes `Tables/aggregate_sale_by_date_category` |

### Expected outcome

Three new Gold Delta tables appear in the lakehouse:

```
Tables/
  aggregate_sale_by_date_city        ~1,460 rows  (one per date × city combination with sales)
  aggregate_sale_by_date_employee    ~730 rows    (one per date × salesperson)
  aggregate_sale_by_date_category    ~1,460 rows  (one per date × city)
```

These are ready to connect to Power BI as a semantic model.

---

## Notebook 4 — Data Discovery (EDA)

**File:** `PakMart - Data Science - Data Discovery.ipynb`

> Run after Notebook 1. Can run in parallel with Notebook 2.

### Why it exists

Before building any ML model you need to understand the data — distributions, outliers, correlations, and whether Pakistani seasonal patterns (Ramadan, Eid) are actually visible. This is pure **exploratory analysis**, producing visualisations that guide feature engineering decisions in Notebook 5.

### What each cell does

| Cell | What it produces |
|---|---|
| Import libraries | matplotlib, seaborn setup |
| Load + sample | Reads all 6 Silver tables; takes a 0.5% random sample (~1,000 rows) for fast plotting |
| `fact_sale.summary()` | Statistical summary table — min/max/mean/stddev for every numeric column |
| Sales by Province | Horizontal bar chart — **Punjab and Sindh dominate** (highest population density) |
| Monthly revenue trend | Line chart across 48 months (2019–2022) — **visible spikes in April/May (Ramadan/Eid) each year** |
| Top 10 products | Side-by-side bars: Revenue vs. Units Sold — large items (fans, pots) top revenue; small items (tea, masala) top units |
| Correlation heatmap | 9×9 heatmap — **TotalIncludingTax strongly correlates with Quantity × UnitPrice**, confirming the ML target is predictable |
| Profit margin by territory | Shows which sales territories have higher margins |

### Expected outcome

5 charts rendered inline in the notebook. Key findings visible:
- Ramadan peaks clearly spike ~40-50% above baseline
- Punjab accounts for ~35% of total revenue
- `TotalIncludingTax` ≈ `Quantity × UnitPrice × 1.17` (17% GST)

---

## Notebook 5 — Pre-processing

**File:** `PakMart - Data Science - Pre-processing.ipynb`

> Run after Notebook 1. Must run before Notebook 6.

### Why it exists

Raw `fact_sale` is a transactional table — it has foreign keys but no contextual features. A model can't use `CityKey=7` to predict anything useful. This notebook **enriches and transforms** the data: joins in province names, derives calendar features (Season, IsFriday, IsWeekend), and filters out anomalous rows. The output is a clean, feature-rich table ready for ML.

### What each cell does

| Cell | What it does |
|---|---|
| Load tables | Reads `fact_sale`, `dimension_city`, `dimension_stock_item`, `dimension_customer`, `dimension_date` from Silver |
| Count raw rows | Prints total: expected ~200,000 (or ~260,000 if incremental was run) |
| Join dimensions | Enriches each sale row with `StateProvince`, `SalesTerritory`, `IsChillerStock`, `Category`, `BuyingGroup`, `FiscalMonthNumber` |
| Feature engineering | Derives 7 new columns: `DayOfWeekName`, `IsWeekend` (0/1), `IsFriday` (0/1, Friday is peak shopping day in Pakistan), `IsChillerItem` (0/1), `Season` (Spring/Summer/Autumn/Winter) |
| Filter anomalies | Removes rows where TotalIncludingTax ≤ 0, Quantity > 1,000, UnitPrice > 500,000 PKR, or extreme losses |
| Count clean rows | Prints final count — typically <0.1% rows removed |
| Save | Writes `pakmart_sale_clean` as a Delta table |
| Display | Shows first 20 rows of the enriched, clean dataset |

### Expected outcome

A new Delta table `pakmart_sale_clean` appears in the lakehouse with ~200,000 rows and these additional columns:

```
StateProvince, SalesTerritory, IsChillerStock, Category, BuyingGroup,
FiscalMonthNumber, DayOfWeekName, IsWeekend, IsFriday, IsChillerItem, Season
```

---

## Notebook 6 — Model Training

**File:** `PakMart - Data Science - Model Training.ipynb`

> Must run after Notebook 5.

### Why it exists

This notebook trains a **LightGBM Regressor** to predict the total sale value (`TotalIncludingTax` in PKR) from transaction features. It uses **MLflow** to track the experiment — logging hyperparameters, evaluation metrics (RMSE, MAE, R²), and the trained model artifact. The registered model can then be loaded by Notebook 7 for batch scoring.

### What each cell does

| Cell | What it does |
|---|---|
| MLflow setup | Creates (or reuses) experiment `pakmart_predict_sale_amount_lightgbm` |
| Sample data | Takes 50% random sample of `pakmart_sale_clean` (~100,000 rows) for faster training |
| Train/test split | 75% train / 25% test, both cached in Spark memory |
| Define features | **Categorical:** SalesTerritory, BuyingGroup, Category, DayOfWeekName, Season — **Numerical:** Quantity, UnitPrice, TaxRate, FiscalMonthNumber, IsChillerItem, IsWeekend, IsFriday |
| Build pipeline | Chains: StringIndexer → OneHotEncoder → VectorAssembler → LightGBMRegressor (label = `TotalIncludingTax`) |
| Hyperparameters | objective=regression, learning_rate=0.05, num_leaves=64, iterations=300, alpha=0.09 |
| Train model | `pipeline.fit(train_df)` — runs LightGBM across the Spark cluster |
| Evaluate | Computes RMSE, MAE, R² on the test set |
| Register model | Logs model + metrics + hyperparameters to MLflow → registers as version 1 of `pakmart_predict_sale_amount_lightgbm` |

### Expected outcome

MLflow experiment logged in the Fabric workspace. Metrics printed:

```
RMSE:  ~1,200–2,500 PKR   (depends on data distribution)
MAE:   ~800–1,800 PKR
R²:    ~0.88–0.96         (high because TotalIncludingTax = Qty × Price × 1.17)
```

In the Fabric left sidebar → **Data science → Experiments** → `pakmart_predict_sale_amount_lightgbm` → view run metrics, parameter comparison, model artifact.

---

## Notebook 7 — Perform Prediction / Scoring

**File:** `PakMart - Data Science - Perform Prediction or Scoring.ipynb`

> Must run after Notebook 6.

### Why it exists

Training a model is only half the job. This notebook demonstrates **batch inference** — loading the registered model from MLflow and applying it to new, unseen data (the 2023 incremental records). The output is a table with both the actual sale values and the model's predicted values, which can be used to flag unusual transactions or forecast revenue.

### What each cell does

| Cell | What it does |
|---|---|
| Load model | Loads version 1 of `pakmart_predict_sale_amount_lightgbm` from the MLflow registry via `mlflow.spark.load_model()` |
| Prepare input | Reads `pakmart_sale_clean` filtered to `Year = 2023`, takes a 25% sample |
| Generate predictions | Calls `loaded_model.transform(input_df)` — adds a `prediction` column |
| Clean output | Drops intermediate pipeline columns (StrIdx, OHEnc, features vector) → renames `prediction` to `PredictedTotalIncludingTax` |
| Display | Shows side-by-side: actual `TotalIncludingTax` vs `PredictedTotalIncludingTax` |
| Save | Writes `pakmart_sale_prediction` as a Delta table |
| Evaluate inference | Computes RMSE and R² on the scored 2023 data — validates model generalises to the new year |

### Expected outcome

Delta table `pakmart_sale_prediction` with ~15,000 rows (25% of 60,000 2023 records), containing:

```
SaleKey, CityKey, ..., TotalIncludingTax (actual), PredictedTotalIncludingTax (model)
```

Inference metrics printed — R² should be close to training R² confirming no overfitting.

---

## Notebook 8 — Semantic Link

**File:** `PakMart - Data Science - Semantic Link.ipynb`

> Run after Notebook 3 (Silver to Gold). Requires a Power BI semantic model built on the Gold tables.

### Why it exists

Once Gold tables are loaded into a Power BI semantic model (`pakmart_gold`), this notebook uses Microsoft's **`sempy`** library (Semantic Link) to query and analyse that model **from inside a Fabric notebook**. It lets you verify that the star-schema relationships were configured correctly in Power BI, and automatically detect hidden functional dependencies within dimension tables (e.g. `EmployeeKey → IsSalesperson`).

### What each cell does

| Cell | What it does |
|---|---|
| `%pip install semantic-link` | Installs the `sempy` package in the Spark session |
| `fabric.list_datasets()` | Lists all Power BI datasets in the workspace — confirms `pakmart_gold` is visible |
| `fabric.list_relationships()` | Returns the 5 m:1 relationships defined in the semantic model: fact_sale → dimension_city / stock_item / date / employee / customer |
| `plot_relationship_metadata()` | Renders a **graph diagram** of the star schema with all FK→PK links drawn |
| `fabric.read_table()` — employee | Reads `dimension_employee` directly from the Power BI model into a pandas DataFrame |
| `employee.find_dependencies()` | Automatically detects functional dependencies — e.g. `EmployeeKey → ValidFrom/ValidTo`, `PreferredName → IsSalesperson` |
| `plot_dependency_metadata()` | Renders a directed graph of those dependencies |
| City dependencies | Same analysis on `dimension_city` — detects `CityKey → StateProvince → SalesTerritory → Region` hierarchy |

### Expected outcome

Three inline visualisations:
1. **Star schema diagram** — `fact_sale` in the centre with 5 dimension tables connected by arrows
2. **Employee dependency graph** — shows `EmployeeKey` as the root, branching to `ValidFrom → Photo`, `Employee/WWIEmployeeID → PreferredName → IsSalesperson`
3. **City dependency graph** — shows the geographic hierarchy `CityKey → City → StateProvince → Region`

> **Prerequisite:** Before running this notebook, you must create a Power BI semantic model in the pakmart workspace that connects to the Gold lakehouse tables. In Fabric: New → Semantic model → name it `pakmart_gold` → add the Gold lakehouse → add the 5 tables → define the 5 relationships.

---

## Complete run checklist

```
□ 1. Sync pakmart workspace in OneLake Explorer
□ 2. Run:  python main.py --mode full --data-root ../pakmart_data
□ 3. Run:  python main.py --mode incremental --data-root ../pakmart_data
□ 4. In Fabric: New → Import notebook → upload all 8 .ipynb files
□ 5. Attach the pakmart lakehouse to every notebook (Add lakehouse → pakmart)

ELT Phase:
□ 6. Run Notebook 1 — Bronze to Silver          → 6 Delta tables created
□ 7. Run Notebook 2 — Incremental Data Load     → fact_sale grows to 260,000 rows
□ 8. Run Notebook 3 — Silver to Gold            → 3 aggregate tables created

Data Science Phase (can run in any order after step 6):
□ 9. Run Notebook 4 — Data Discovery            → 5 charts, data profiled
□ 10. Run Notebook 5 — Pre-processing           → pakmart_sale_clean table
□ 11. Run Notebook 6 — Model Training           → MLflow model registered
□ 12. Run Notebook 7 — Prediction/Scoring       → pakmart_sale_prediction table

After Power BI semantic model is built:
□ 13. Run Notebook 8 — Semantic Link            → relationship + dependency graphs
```

---

## Tables created after full run

| Table | Layer | Rows | Description |
|---|---|---|---|
| `dimension_city` | Silver | 30 | Pakistani cities with provinces, territories |
| `dimension_customer` | Silver | 500 | Pakistani businesses |
| `dimension_date` | Silver | 1,461 | 2019–2022 with Pakistani fiscal year |
| `dimension_employee` | Silver | 25 | Salespersons and staff |
| `dimension_stock_item` | Silver | 58 | Products in PKR |
| `fact_sale` | Silver | 260,000 | Transactions 2019–2023 (after incremental) |
| `aggregate_sale_by_date_city` | Gold | ~1,460 | Daily revenue by province/territory |
| `aggregate_sale_by_date_employee` | Gold | ~730 | Daily revenue by salesperson |
| `aggregate_sale_by_date_category` | Gold | ~1,460 | Daily revenue by city |
| `pakmart_sale_clean` | ML | ~200,000 | Feature-engineered, outliers removed |
| `pakmart_sale_prediction` | ML | ~15,000 | 2023 data with predicted sale amounts |

---

## Can you upload the notebook files from here?

**Yes.** The `.ipynb` files are valid Jupyter/Fabric notebooks stored locally at:

```
f:\siddi\msfabric_retails_data\
  PakMart - Data Transformation - Bronze to Silver.ipynb
  PakMart - Data Transformation - Incremental Data Load.ipynb
  PakMart - Data Transformation - Silver to Gold.ipynb
  PakMart - Data Science - Data Discovery.ipynb
  PakMart - Data Science - Pre-processing.ipynb
  PakMart - Data Science - Model Training.ipynb
  PakMart - Data Science - Perform Prediction or Scoring.ipynb
  PakMart - Data Science - Semantic Link.ipynb
```

### Upload method 1 — Fabric UI (easiest)

1. Open the **pakmart** workspace in Fabric
2. Click **New → Import notebook**
3. Click **Upload** and select all 8 files at once
4. Done — they appear in the workspace immediately

### Upload method 2 — OneLake Explorer (drag and drop)

Notebooks are stored in OneLake at `<workspace>/Notebooks/`. You can copy the `.ipynb` files directly into:

```
C:\Users\Admin\OneLake - Microsoft\pakmart\<NotebookName>.SynapseNotebook\
```

However, the **Fabric UI import** (Method 1) is simpler and more reliable.

### Upload method 3 — Fabric REST API

If you need to automate this, the Fabric API supports notebook creation:

```bash
# Using the Fabric REST API (requires access token)
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/notebooks
Content-Type: application/json
{
  "displayName": "PakMart - Data Transformation - Bronze to Silver",
  "definition": { ... base64-encoded notebook content ... }
}
```

For now, **Method 1 (UI upload) is all you need** — select all 8 files at once, they upload in seconds.
