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
| UTA GTFS snapshots (feed `mdb-170`) | `_data/remote/gtfs/*.zip` (+ `_data/remote/mdb-170_datasets.json` listing) | Mobility Database API, `gis_adhoc_analyses.mobility_database` | Snapshots in effect during 2026; published schedules end 2026-12-05 | ⚠️ | Dec 6-31 projected; delete the listing JSON and re-render once UTA's December feed is archived |
