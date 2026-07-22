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
| REMM parcels table | `_data/raw/remm/` (filename TBD) | REMM model output, pickle -- provided manually | TBD | 🔴 | Waiting on file from Pukar. Large file, gitignored explicitly (not superseded by a REST equivalent). |
| REMM buildings table (2055, incl. `built_yr`) | `_data/raw/remm/` (filename TBD) | REMM model output, pickle -- provided manually | TBD | 🔴 | Same as above. Need `built_yr`, `parcel_id`, and land-use/space-type fields to split residential vs. commercial/employment for the 2050/2055 development-mix ratio. |
| The Point development schedule | `_data/raw/` (format TBD) | Provided by The Point team | TBD | 🔴 | Full buildout plan/schedule -- confirm whether it covers 100% of the center's developable area or leaves a residual to estimate. |
