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
| WFTDM Transportation Analysis Zones | `_data/remote/wftdm_taz_v10.gpkg` | `WasatchFrontTAZ` REST service (key `wftcm_taz`) | v10 | ✅ | |
| Socioeconomic (SE) forecast | `_data/raw/SE_v10_20260921/SE_{year}.csv` | Suzie, direct file (not REST) | v10, 2023-2065 | ✅ | |
| Utah Bikeways | `_data/remote/utah_bikeways.gpkg` | OpenSGID/UGRC `Bikeways` REST service | Live REST | ✅ | Bike 2027 base, filtered to exclude `Facility1` "Not Available" and the class-3 shared-roadway/shoulder family (matches v9 `_archive/` script's code exclusions) |
| UTA stops | `_data/remote/uta_stops.gpkg` | RideUTA `UTA_Stops_and_Most_Recent_Ridership` REST service | Live REST | ✅ | Transit 2027 base |
| UTA routes | `_data/remote/uta_routes.gpkg` | RideUTA `UTA_Routes_and_Most_Recent_Ridership` REST service | Live REST | ✅ | Transit 2027 base (frequent-route filter) |
| RTP 2027 AT projects (lines/points) | `_data/remote/projects/at_lines.gpkg`, `at_points.gpkg` | WFRC `RTP2027_PreferredScenario_092026_PUBLIC` REST service | Sept 2026 draft | ✅ | Bike 2032 (`Field9_STIP = 1`) and 2055 (`phase` <> 0, unfunded phase 0 excluded) additions, filtered locally at read time; re-download periodically, still a draft. Switched from the private June 2026 draft (`RTP2027_PreferredScenario_062026`) to the public Sept 2026 vintage |
| Bike 2032 vintage | `_data/remote/projects/at_lines.gpkg` | RTP AT line projects with `Field9_STIP = 1` | Sept 2026 draft | ✅ | Closed -- STIP-flagged RTP projects are the final 2032 bike definition |
| WF TDM MasterNet (transit networks) | `_data/raw/WFv1000_MasterNet_20260903.gdb` | Suzie, direct file (Cube MasterNet export, not REST) | v10, 2026-09-03 (2032 + 2055 transit networks) | ✅ | Corrected 2026-10-13 (re-imported `wfrc_core_2032` [new], `rail_2032`, `wfrc_brt_2032/2055`, `wfrc_sl_lcl_2032/2055`): OGX named `O603X` in both years, `S240` 30 min in 2032. Known open item: Mid-Valley Express is `S050X` in 2032 but `MidValCon` in 2055 (naming only, no effect on results). 2036/2046 transit stop data still pending -- those scenarios reuse 2032. Transit 2032 and 2055 vintages: `{group}_{year}_PTNode` stops (`STOPNODE = 1`) joined to `_PTLine` route `MODE`/`HEADWAY_1`, kept if rail/BRT (modes 7-9) or local/core bus (modes 4-5) at ≤15 min. Highway Node/Link layers unused |
| Workshop Areas boundary | n/a | v9 used a `\\server1\...` network shapefile | n/a | 🔴 | No v10 source identified -- workshop-area geography level not reported |
| `_archive/` (v9 scripts, TAZ.shp, SE_v9 files) | n/a | v9 project archive | 2023 RTP vintage | 📦 | Reference only, gitignored -- not a deliverable |
