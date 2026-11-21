# MAZ Numbering

Assigns a new, consecutive `MAZID` (1 to N) to every microzone (MAZ) in the
Wasatch Front travel demand model. Ported from
`joa-wfrc/TDM-GEO-maz_numbering`; the geometry cleanup step in that repo is
out of scope here -- the input MAZ layer is assumed already cleaned.

## Numbering rules

1. Each MAZ is located by its **representative point** (always inside the polygon).
2. `TAZID` comes from a **point-in-polygon** join of that point to the TAZ layer.
3. MAZs are numbered **TAZ by TAZ**, in ascending `TAZID`.
4. Within a TAZ: **north to south, then west to east** (strict sort on Y descending, then X ascending).
5. `MAZID` is one sequence for the whole region, 1 to N, no gaps.
6. The previous ID is kept in `MAZID_OLD` for comparison and QC, and dropped just before the shapefile is exported.

All spatial work is in EPSG:26912.

## Data sources

See `sources.md`. The official `WFv1000_TAZ.shp` (from `TDM-GEO-AnalysisZones`) and the cleaned MAZ (zipped shapefile) are both manual files in `_data/raw/`; nothing is downloaded.

## Layout

```
_data/
  raw/         WFv1000_TAZ.* -- official TAZ shapefile; Microzones_Clean_20261120.zip -- cleaned MAZ (git-tracked)
  remote/      (unused -- no REST layers)
  processed/   intermediate outputs -- gitignored
output/        WFv1000_MAZ.shp, WFv1000_MAZ_qc_map.html
index.qmd      renders as a page on the site
```

## Running

```bash
uv run quarto render projects/maz-numbering/index.qmd
```

Shapefile field names are limited to 10 characters.
