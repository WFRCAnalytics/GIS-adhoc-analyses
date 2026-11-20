# uta-transit-vmt-2026

## What / why

Scheduled annual transit vehicle miles of travel (VMT) for UTA in 2026 by mode (Local Bus, Express Bus, BRT, Light Rail, Commuter Rail; Microtransit separately), computed from archived GTFS feeds in the Mobility Database. Requires `MOBILITY_DATABASE_REFRESH_TOKEN` in `.env`.

## Data sources

GTFS snapshots downloaded via `gis_adhoc_analyses.mobility_database` (see `sources.md`). `sources.yml` is intentionally empty -- no ArcGIS layers.

## Layout

```
_data/
  raw/         offline/manual source data -- git-tracked
  remote/      REST-downloaded via ensure_layers() -- gitignored, reproducible.
               Delete a .gpkg to force a fresh download.
  processed/   intermediate outputs -- gitignored
output/        final deliverables (CSV/GeoJSON/figures) -- git-tracked by default
index.qmd      renders as a page on the site
```

## Running

```bash
uv run quarto preview projects/<name>/index.qmd
```
