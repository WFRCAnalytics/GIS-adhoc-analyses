# Transportation Choices

Percent of the WFRC-region population within 1/4 mile of a dedicated bike
facility, or a frequent bus route / transit stop / station, across three
scenarios (Existing 2027, No Build 2055, RTP 2055). Replaces the `_archive/`
v9 arcpy scripts, which bundled socioeconomic (SE) data and GIS facility
data together per scenario instead of letting them vary independently.

## Data sources

See `sources.yml` (machine-readable registry) and `sources.md` (human
registry with vintage/status/contact), and the "Data Sources" section of
`index.qmd` for how each layer maps to a scenario. Run cells in `index.qmd`
to download via `gis_adhoc_analyses.layer_cache.ensure_layers()`.

SE data (`_data/raw/SE_v10_20260921/`, one CSV per year 2023-2065) was
provided directly by Suzie -- not REST-backed.

## Layout

```
_archive/      v9 reference scripts/data -- gitignored, research only
_data/
  raw/         SE v10 CSVs -- git-tracked
  remote/      REST-downloaded via ensure_layers() -- gitignored, reproducible.
               Delete a .gpkg to force a fresh download.
  processed/   intermediate outputs -- gitignored
output/        one CSV per scenario -- git-tracked
index.qmd      renders as a page on the site
```

## Running

```bash
uv run quarto preview projects/transportation-choices/index.qmd
```
