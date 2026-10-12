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
| RTP 2027 Transit projects (lines/points) | `_data/remote/projects/transit_lines.gpkg`, `transit_points.gpkg` | WFRC `RTP2027_PreferredScenario_092026_PUBLIC` REST service | Sept 2026 draft | ✅ | Transit 2032 (`Field9_STIP = 1`) and 2055 (`phase` <> 0, unfunded phase 0 excluded) additions, filtered locally at read time; re-download periodically, still a draft. Switched from the private June 2026 draft (`RTP2027_PreferredScenario_062026`) to the public Sept 2026 vintage |
| Bike 2032 vintage | `_data/remote/projects/at_lines.gpkg` | RTP AT line projects with `Field9_STIP = 1` | Sept 2026 draft | ✅ | Closed -- STIP-flagged RTP projects are the final 2032 bike definition |
| TDM stops (transit 2032 vintage) | n/a | Suzie | n/a | ⚠️ | Pending -- `GIS_VINTAGES["transit"][2032]` uses RTP transit projects with `Field9_STIP = 1` as an interim stand-in |
| Workshop Areas boundary | n/a | v9 used a `\\server1\...` network shapefile | n/a | 🔴 | No v10 source identified -- workshop-area geography level not reported |
| `_archive/` (v9 scripts, TAZ.shp, SE_v9 files) | n/a | v9 project archive | 2023 RTP vintage | 📦 | Reference only, gitignored -- not a deliverable |
