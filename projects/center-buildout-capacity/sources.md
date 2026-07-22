# Data Sources Registry

Tracks every input dataset used by this analysis. Companion to `sources.yml`
(machine-readable) -- this file is the human-readable record of vintage,
status, and who to contact when a source goes stale.

**Status legend**

| Symbol | Meaning |
|---|---|
| ✅ | Current -- no action needed |
| ⚠️ | Placeholder or potentially stale -- verify/replace before final run |
| 🔴 | Missing / blocked -- data not yet received |
| 📦 | Archived -- kept for reference, superseded by a REST-downloaded layer |

---

| Dataset | Cache path | Source | Vintage | Status | Contact / Action |
|---|---|---|---|---|---|
| Center boundaries (Daybreak, Saratoga Springs Downtown, The Point -- Urban Center polygon only) | `_data/remote/center_boundaries.gpkg` | WFRC `WCV_Centers_and_Regional_Land_Uses` REST service | Live REST | ✅ | Server-side filtered via `where` in `sources.yml`. The Point's Employment District polygon is intentionally excluded. |
| REMM base-year parcels | `_data/raw/remm/remm_base_year_data.gdb` (`parcels` layer) | REMM model output, FileGDB -- provided manually | 2023 base year | ✅ | Cached as GeoParquet at `_data/processed/parcels_2023.parquet`. |
| REMM buildings table (2055, incl. `year_built`) | `_data/raw/remm/run1842year2055allbuildings.pkl` | REMM model output, pickle -- provided manually | 2055 run | ✅ | Cached as GeoParquet/parquet at `_data/processed/buildings_2055.parquet` (full 150-column replica). |
| The Point development schedule | `_data/raw/` (format TBD) | Provided by The Point team | TBD | 🔴 | Full buildout plan/schedule -- confirm whether it covers 100% of the center's developable area or leaves a residual to estimate. |
