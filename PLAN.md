# GIS-adhoc-analyses: repo scaffold

## Context

This repo holds many small, one-off GIS analyses over time — each self-contained enough to track code/process/results in git, without the overhead of bootstrapping a new repo per analysis. Initial design was refined after reviewing `WFRCAnalytics/GIS-RTP-Phasing-Criteria`, an existing WFRC repo the user pointed to as inspiration for handling ArcGIS REST data. That repo's patterns are adopted directly below, with attribution noted per section.

Confirmed decisions:

- **Single shared root Python environment** (uv-managed, Python 3.14) used by every subfolder — not per-subfolder venvs.
- **No Esri `arcgis` SDK.** The reference repo explicitly abandoned it ("no arcgis SDK required" — see its `_src/arcgis_utils.py` docstring; its `pyproject.toml` has no `arcgis` dependency at all) in favor of a `requests`-based downloader with objectId batching. We adopt the same approach — it sidesteps the exact dependency-conflict history the user described, and it's a proven pattern from WFRC's own repo.
- **Full Quarto website scaffold now**, single root-level site, using the WFRC brand extension (`WFRCAnalytics/wfrc-brand`).
- **Publishes to `docs/`** — `output-dir: docs` + `site-url` set in `_quarto.yml` so GitHub Pages can serve directly from `main`/`docs` with no CI/build step (decided after initial "local preview only" choice, once it was clear `docs/` needs no Actions workflow). `docs/` is tracked in git; `_freeze/` stays gitignored since renders happen locally with live data access rather than in CI.

Environment already confirmed on this machine: `uv 0.10.8` can install `cpython-3.14.3` directly (no conda involved), and `quarto 1.9.38` is on PATH.

## Patterns adopted from `GIS-RTP-Phasing-Criteria`

| Pattern | What it is | Adaptation for this repo |
|---|---|---|
| `requests`-based ArcGIS downloader | `_src/arcgis_utils.py`: objectId-batched fetch (avoids `exceededTransferLimit` issues), `.env`-based token auth for secured layers, ZIP/GDB support via GDAL `/vsizip/` | Ported into `src/gis_tools/arcgis_utils.py`, near-verbatim (same org, explicitly requested as inspiration) |
| `sources.yml` + `layer_cache.py` | Central registry of REST URLs → local `.gpkg` cache paths; `ensure_layers(keys)` downloads what's missing, prints cache age otherwise | One `sources.yml` **per project** (not repo-global, since projects are unrelated) + shared `src/gis_tools/layer_cache.py`. Cache paths resolved relative to each project's own `sources.yml`, not a hardcoded repo root — makes `_template` truly copy-paste portable |
| `sources.md` | Human-readable registry: dataset, cache path, vintage, status (✅⚠️🔴), contact/action | One per project, same convention |
| `_data/{raw,remote,processed}` split | `raw` = offline sources, git-tracked; `remote` = REST-downloaded cache, gitignored (delete file to force refresh); `processed` = intermediate outputs, gitignored | Same, per-project under `projects/<name>/_data/` |
| GeoPackage as cache format | `.gpkg` via `gdf.to_file(cache_path, driver="GPKG")` | Same |
| `.env` / `.env.example` for credentials | `ARCGIS_USERNAME`, `ARCGIS_PASSWORD`, optional `ARCGIS_PORTAL_URL` | Same, at repo root (shared across projects); `.env` already covered by existing `.gitignore` |
| Underscore-prefixed dirs auto-excluded by Quarto | `_data/`, `_extensions/`, etc. never scanned as pages | Same — means `_template/` (underscore-prefixed) is also auto-excluded from the site without extra `_quarto.yml` render rules |
| `freeze: auto` | Caches notebook execution output so re-renders don't always re-run REST downloads/geoprocessing | Same, but `_freeze/` stays gitignored for now (not publishing) — documented as a flip-later item |

## Target layout

```
GIS-adhoc-analyses/
├── .env.example
├── .gitignore                  # extended, see below
├── .python-version              # "3.14"
├── pyproject.toml
├── uv.lock
├── README.md
├── CLAUDE.md                    # dev conventions, mirrors reference repo's approach
├── _quarto.yml
├── index.qmd
├── _extensions/
│   └── WFRCAnalytics/wfrc-brand/   # via `quarto add WFRCAnalytics/wfrc-brand`
├── src/
│   └── gis_tools/
│       ├── __init__.py
│       ├── arcgis_utils.py      # fetch_feature_layer, download_layer, download_zip_layer, generate_token
│       └── layer_cache.py       # ensure_layers(keys, sources_path="sources.yml", force=False, token=None)
└── projects/
    └── _template/                # copy this folder to start a new analysis
        ├── README.md             # what/why/data sources for this analysis
        ├── sources.yml           # this project's ArcGIS REST layers
        ├── sources.md            # human registry: vintage/status/contact
        ├── index.qmd             # renders as a page on the site
        ├── _data/
        │   ├── raw/.gitkeep
        │   ├── remote/.gitkeep
        │   └── processed/.gitkeep
        └── output/.gitkeep
```

New analysis = `cp -r projects/_template projects/<name>`, fill in `sources.yml`/`sources.md`, add a nav entry in `_quarto.yml`.

## Root Python project (`pyproject.toml`)

- `uv init --package .` → src layout so `import gis_tools` works from any project via `uv run`.
- `requires-python = "==3.14.*"`.
- Dependencies: `pandas`, `geopandas`, `pyogrio`, `duckdb`, `requests`, `pyyaml`, `python-dotenv`, `jupyter`, `ipykernel`. No `arcgis` package. This is a much more standard combination than the original plan (which included the heavy `arcgis` SDK), so dependency-resolution risk on Python 3.14 is low — still verified empirically as step 1 of execution.
- One-off/unusual packages needed by a single analysis: add directly to root deps, or `uv run --with <pkg>` for a throwaway need.

## `src/gis_tools/arcgis_utils.py` and `layer_cache.py`

Adapted from the reference repo's `_src/arcgis_utils.py` / `_src/layer_cache.py`, **hardened against a known ArcGIS REST gotcha**: for query-layer / SQL-view / joined services (common for ridership or joined attribute tables), the server can regenerate OBJECTIDs non-deterministically between requests, so a plain "get ID list, then fetch each batch by ID" approach can silently duplicate, drop, or reorder rows if the two calls don't see the same ID assignment. Plain `resultOffset` pagination has the analogous failure if you assume a fixed page size instead of checking what was actually returned. This matches the ordering/duplication issue previously hit, so the downloader treats it as the default risk to guard against, not an edge case:

- `fetch_feature_layer(service_url, out_sr=4326, where="1=1", out_fields="*", token=None) -> GeoDataFrame`:
  1. Query service info for `maxRecordCount` and the actual `objectIdFieldName` (not assumed to be `"OBJECTID"` — some services use `FID` or a custom name).
  2. Fetch all matching objectIds (`returnIdsOnly=true`) and **sort them** — makes batching deterministic and reproducible run-to-run instead of relying on server-returned order.
  3. Batch-fetch by objectId (POST, avoids URI-too-long). Each batch's response IDs are checked against the requested IDs; any batch that comes back short is retried once (with backoff) before giving up on the missing IDs — protects against transient partial responses being silently accepted as complete.
  4. **After concatenating all batches**: drop exact duplicate rows on `objectIdFieldName`, warning with a count if any were found (signals server-side ID instability rather than a bug in our loop).
  5. **Verify**: compare the final unique-ID count against the count from step 2. Mismatch → raise (fewer = silently dropped data, which is worse than a slow failure) rather than returning a partial GeoDataFrame unflagged.
  - Optional `order_by: str | None` param: for layers known to have unstable OBJECTIDs (flag with `pagination: offset` in `sources.yml`), falls back to `resultOffset` pagination with an explicit `orderByFields` on a genuinely stable attribute (never OBJECTID for these layers), incrementing by the *actual* record count returned each page (not the requested page size) and stopping on `exceededTransferLimit: false` — same final dedupe/verify steps apply regardless of which path was used.
- `generate_token(username=None, password=None, portal_url=None)` — reads `ARCGIS_USERNAME`/`ARCGIS_PASSWORD`/`ARCGIS_PORTAL_URL` from `.env` via `python-dotenv`, posts to `/sharing/rest/generateToken`.
- `download_layer(cache_path, service_url, force=False, token=None, **fetch_kwargs)` — skips download if cache exists and isn't forced; warns (doesn't auto-refresh) if cache is >1 year old.
- `download_zip_layer(cache_path, url, layer_name=None, gdb_name=None, where=None, force=False)` — downloads a ZIP once, reads shapefile/GDB layer via GDAL `/vsizip/`, writes `.gpkg`.
- `ensure_layers(keys, sources_path="sources.yml", force=False, token=None) -> dict[str, Path]` — loads the project's `sources.yml`, resolves each `cache:` path **relative to `sources_path`'s directory** (the one deliberate deviation from the reference implementation, which hardcodes repo-root-relative paths — this keeps each project folder self-contained and copy-paste portable), downloads what's missing, returns `{key: Path}`. Passes through a per-layer `pagination:` and `order_by:` from `sources.yml` to `fetch_feature_layer`.

Usage inside a project's `index.qmd`:
```python
from gis_tools.layer_cache import ensure_layers
L = ensure_layers(["bikeways"])   # reads ./sources.yml, writes into ./_data/remote/
bikeways = gpd.read_file(L["bikeways"])
```

## `projects/_template/sources.yml` (example entry)

```yaml
layers:
  example_layer:
    url: https://services.arcgis.com/.../FeatureServer/0
    cache: _data/remote/example_layer.gpkg
    description: Short human-readable label
    # access: private        # uncomment if the layer needs a token
    # where: "STATUS = 'Active'"
    # pagination: offset     # uncomment for query-layer/joined services with unstable OBJECTIDs
    # order_by: SomeStableField  # required if pagination: offset is set
```

## Quarto site

- `quarto add WFRCAnalytics/wfrc-brand` at repo root → `_extensions/WFRCAnalytics/wfrc-brand/`.
- `_quarto.yml`: `project: type: website`, `output-dir: docs`; `brand: _extensions/WFRCAnalytics/wfrc-brand/brand.yml`; theme SCSS wired the same way as the reference `format.html.theme.light/dark`; `freeze: auto`; `site-url: https://wfrcanalytics.github.io/GIS-adhoc-analyses`; navbar linking `index.qmd` + `projects/_template/index.qmd` as a proof-of-concept page.
- `index.qmd`: brief landing page listing analyses.
- `projects/_template/index.qmd`: minimal example page with one executable Python cell that calls `ensure_layers()` against a small real public layer and renders a `geopandas` plot/table — proves the Python ↔ ArcGIS ↔ Quarto ↔ brand pipeline end to end.

## `.gitignore` additions

```gitignore
# Quarto
/.quarto/
**/*.quarto_ipynb
_freeze/

# Per-project data (ad hoc analyses: remote/processed are reproducible caches;
# raw is tracked by default — add explicit per-file excludes here if a raw
# source exceeds ~50-100MB and is superseded by a REST-cached equivalent)
projects/*/_data/remote/*
!projects/*/_data/remote/.gitkeep
projects/*/_data/processed/*
!projects/*/_data/processed/.gitkeep
```

(`.env` is already covered by the existing `.gitignore`'s "Environments" section.)

## `CLAUDE.md` (root)

Short dev-conventions doc, mirroring the reference repo's `CLAUDE.md` Development section: `uv sync` to set up, `uv run quarto preview <file>` to render, the `sources.yml`/`ensure_layers()` pattern with a code example, the `_data` gitignore convention, and "copy `projects/_template`" as the way to start a new analysis.

## README.md (root)

Purpose of the repo, quickstart (`uv sync`, `uv run python projects/<name>/script.py` or `uv run quarto preview`), how to start a new analysis, the gitignore convention, and a pointer to `CLAUDE.md` for fuller conventions.

## Verification

1. `uv sync` succeeds on Python 3.14 with no resolution errors.
2. `uv run python -c "import gis_tools, geopandas, duckdb, requests, yaml, dotenv; print('ok')"` succeeds.
3. `uv run python -c "from gis_tools.layer_cache import ensure_layers; ..."` against `projects/_template/sources.yml` pointed at a real small public ArcGIS FeatureServer layer — proves the downloader works end to end, not just imports.
4. `uv run quarto preview` renders the site locally without error, brand theme visibly applied, `projects/_template/index.qmd` executes its Python cell and renders output.
5. `git status` reviewed so only intended files are tracked (`_data/remote` and `_data/processed` correctly ignored, `.gitkeep` placeholders present, `_data/raw` tracked).
