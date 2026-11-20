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
| WFTDM Transportation Analysis Zones | `_data/remote/wftdm_taz.gpkg` | `WasatchFrontTAZ` REST service (key `wftdm_taz`) | Live REST | ✅ | |
| Cleaned microzones (MAZ) | `_data/raw/Microzones_Clean.zip` | Zipped shapefile provided directly by Joa (not REST) | Received 2026-11-13 | ✅ | Output of the (out-of-scope) geometry cleanup. To refresh, replace the zip |
