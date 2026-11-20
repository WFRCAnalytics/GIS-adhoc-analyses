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
| WFTDM Transportation Analysis Zones | `_data/remote/wftdm_taz.gpkg` | `WasatchFrontTAZ` REST service (key `wftdm_taz`) | Live REST | ✅ | Service is natively EPSG:3857. Requested with `out_sr: 26912` so the server projects it once; matches the authoritative `TDM-GEO-AnalysisZones` `WFv1000_TAZ.shp` to within ~0.07 m2 per zone. Without `out_sr` the layer arrives as 4326 and a `to_crs(26912)` round trip shifts geometry by roughly a meter |
| Cleaned microzones (MAZ) | `_data/raw/Microzones_Clean_20261120.zip` | Zipped shapefile provided directly by Josh (not REST) | Received 2026-11-20, revised same day (supersedes the 2026-11-13 file: 14,164 MAZs vs 14,199, `DEVACRES`/`DEVPBLEPCT` fields dropped) | ✅ | Output of the (out-of-scope) geometry cleanup. To refresh, replace the zip and update the path in `index.qmd` |
