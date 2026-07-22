# _template

Copy this folder to start a new ad hoc analysis: `cp -r projects/_template projects/<name>`.

## What / why

Replace this section with: what question this analysis answers, who asked
for it, and any deadline or downstream use.

## Data sources

See `sources.yml` (machine-readable registry) and `sources.md` (human
registry with vintage/status/contact). Run cells in `index.qmd` to download
via `gis_tools.layer_cache.ensure_layers()`.

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
