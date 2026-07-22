# center-buildout-capacity

## What / why

Estimates additional housing units and jobs at full buildout for three WCV
centers:

- **Daybreak** ("Downtown Daybreak") and **Saratoga Springs Downtown**:
  identify parcels within the center boundary that REMM develops or
  redevelops after 2025 (excluding development already reflected in the
  post-base-year housing inventory), sum their acreage as the developable /
  redevelopable land base, derive the forecast residential vs.
  commercial/employment development mix (2050 or 2055) from REMM, and apply
  median center-level dwelling-unit-per-acre and employment-density (FAR +
  job-space) assumptions to that mix to estimate buildout capacity.
- **The Point**: report the full buildout from the development schedule
  provided directly by The Point team; estimate any residual undeveloped
  area only if their schedule doesn't cover 100% of the center.

## Data sources

See `sources.yml` (machine-readable registry) and `sources.md` (human
registry with vintage/status/contact). Run cells in `index.qmd` to download
via `gis_adhoc_analyses.layer_cache.ensure_layers()`.

REMM parcels/buildings tables and The Point's development schedule are
provided manually (not REST-downloadable) -- see `_data/raw/` below and
`sources.md` for what's still outstanding.

## Layout

```
_data/
  raw/         offline/manual source data -- git-tracked by default
    remm/      REMM parcels + buildings pickle tables -- manually placed,
               gitignored explicitly (large files; see root .gitignore)
  remote/      REST-downloaded via ensure_layers() -- gitignored, reproducible.
               Delete a .gpkg to force a fresh download.
  processed/   intermediate outputs -- gitignored
output/        final deliverables (CSV/GeoJSON/figures) -- git-tracked by default
index.qmd      renders as a page on the site
```

## Running

```bash
uv run quarto preview projects/center-buildout-capacity/index.qmd
```
