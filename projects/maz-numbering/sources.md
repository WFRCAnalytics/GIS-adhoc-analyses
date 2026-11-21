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
| Official TAZ (`WFv1000_TAZ`) | `_data/raw/WFv1000_TAZ.*` | `TDM-GEO-AnalysisZones` releases repo, `data/taz/` (commit `bbc9771`, pre-release v10.0.0-beta2, 2026-10-09), copied unchanged | WFv1000 pre-release | ✅ | Already EPSG:26912, 3,562 TAZs. Replaces the REST `WasatchFrontTAZ` layer, which is natively EPSG:3857 and does not match the official geometry exactly. To refresh, re-copy the files from that repo |
| Cleaned microzones (MAZ) | `_data/raw/Microzones_Clean_20261120.zip` | Zipped shapefile provided directly by Josh (not REST) | Received 2026-11-20, revised same day (supersedes the 2026-11-13 file: 14,164 MAZs vs 14,199, `DEVACRES`/`DEVPBLEPCT` fields dropped) | ✅ | Output of the (out-of-scope) geometry cleanup. To refresh, replace the zip and update the path in `index.qmd` |
