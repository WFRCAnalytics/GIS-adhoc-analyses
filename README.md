# GIS-adhoc-analyses

Small, one-off GIS analyses for WFRC -- each self-contained enough to track
code, process, and results in git, without the overhead of a full separate
repo per analysis.

## Setup

```bash
uv sync
quarto add WFRCAnalytics/wfrc-brand   # already installed; re-run after a clean clone if _extensions/ is missing
```

## Starting a new analysis

```bash
cp -r projects/_template projects/<name>
```

Fill in `projects/<name>/sources.yml` and `sources.md` with the ArcGIS REST
layers (or other sources) the analysis needs, write the analysis in
`index.qmd` (or a plain `.py` script), and add a navbar entry in `_quarto.yml`.

## Running an analysis

```bash
uv run quarto preview projects/<name>/index.qmd   # single page, live reload
uv run quarto preview                              # whole site
```

## Publishing

`uv run quarto render` builds the whole site into `docs/`, which is tracked
in git. Commit and push `docs/` to publish -- GitHub Pages serves it
directly from `main`/`docs` with no CI/build step. Enable it once under repo
Settings -> Pages -> Source: `main` branch, `/docs` folder.

## Downloading ArcGIS REST data

Every project calls `gis_tools.layer_cache.ensure_layers()` against its own
`sources.yml`:

```python
from gis_tools.layer_cache import ensure_layers
import geopandas as gpd

L = ensure_layers(["some_layer_key"])
gdf = gpd.read_file(L["some_layer_key"])
```

See `src/gis_tools/arcgis_utils.py` for the downloader itself -- plain
`requests` (no Esri SDK), objectId-batched with dedup/ordering safeguards for
services that don't behave consistently across requests.

Secured/private layers need `ARCGIS_USERNAME` / `ARCGIS_PASSWORD` in a local
`.env` (copy `.env.example`) -- never commit `.env`.

## Data conventions

Per project, under `projects/<name>/_data/`:

| Folder | Tracked? | Contents |
|---|---|---|
| `raw/` | yes (by default) | Offline/manual source data. Exclude individual files in `.gitignore` if they exceed ~50-100MB and are superseded by a REST-cached equivalent. |
| `remote/` | no | REST-downloaded via `ensure_layers()`. Delete a `.gpkg` to force a fresh download. |
| `processed/` | no | Intermediate outputs. |

`projects/<name>/output/` holds final deliverables (CSV/GeoJSON/figures) and
is tracked by default.

See `CLAUDE.md` for fuller development conventions.
