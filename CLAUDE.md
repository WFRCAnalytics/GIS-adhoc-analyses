# CLAUDE.md

This file provides guidance to Claude Code (and other agents) when working
in this repository.

## Overview

This repo hosts many small, unrelated ad hoc GIS analyses for WFRC, each
under `projects/<name>/`. There is no single overarching project -- treat
each `projects/<name>/` folder as its own scoped task, but sharing one
Python environment and one set of downloader utilities.

## Environment

- **Package manager**: `uv` -- do not use `conda` or `pip` directly.
- **Python**: 3.14, pinned in `.python-version`.
- **Setup**: `uv venv --prompt "GIS-adhoc-analyses"` then `uv sync` -- the
  explicit `--prompt` must come first. `uv sync` alone would create the venv
  itself and set the prompt from the PEP 503-normalized project name
  (`gis-adhoc-analyses`, lowercase) instead of the literal repo casing; once
  the venv already exists with an explicit prompt, `uv sync` leaves it alone.
- **Render a page**: `uv run quarto render <path/to/index.qmd>`
- **Preview interactively**: `uv run quarto preview <path/to/index.qmd>`
- **Lint/format** (`.py` files only -- ruff doesn't parse `.qmd` code fences):
  `uv run ruff check --fix .` and `uv run ruff format .`. Config lives in
  `[tool.ruff]` in `pyproject.toml`.
- One-off packages needed by a single analysis: add to root `pyproject.toml`
  via `uv add <pkg>`, or use `uv run --with <pkg>` for a throwaway need.
  There are no per-project virtual environments.

## Starting a new analysis

```bash
cp -r projects/_template projects/<name>
```

Then fill in `sources.yml`/`sources.md`, write `index.qmd`, and add a navbar
entry in the root `_quarto.yml`.

## ArcGIS REST data (`sources.yml` + `gis_adhoc_analyses`)

Each project defines its own `sources.yml` (url + local `.gpkg` cache path +
description, per layer -- see `projects/_template/sources.yml` for the
schema and `sources.md` for the human-readable vintage/status registry).

Call `ensure_layers()` at the top of a project's data-loading section:

```python
from gis_adhoc_analyses.layer_cache import ensure_layers
L = ensure_layers(["some_layer_key"])
gdf = gpd.read_file(L["some_layer_key"])
```

- Force re-download of specific layers: `ensure_layers([...], force=["key"])`
- Force re-download of everything requested: `ensure_layers([...], force=True)`
- Secured layers (`access: private` in sources.yml): put credentials in
  `.env` (copy `.env.example`); a token is generated automatically.

**Do not use the Esri `arcgis` SDK.** `src/gis_adhoc_analyses/arcgis_utils.py`
talks to the ArcGIS REST API directly via `requests` -- deliberately, to avoid the
SDK's heavy/pinned dependency tree conflicting with geopandas/duckdb, and to
guard against a known failure mode: query-layer/joined services can
regenerate OBJECTIDs non-deterministically between requests, which silently
duplicates, drops, or reorders rows under naive pagination. See the module
docstring for the specific mitigations (sorted IDs, batch-response
verification, post-fetch dedup, count verification, and an `offset` pagination
fallback for layers with unstable OBJECTIDs). Extend this module rather than
reaching for the SDK or writing a one-off pagination loop in a notebook.

## Data folder conventions

Per project, under `projects/<name>/_data/`:

- `raw/` -- offline/manual source data, git-tracked by default. Add explicit
  per-file excludes to the root `.gitignore` if a raw file exceeds ~50-100MB
  and is superseded by a REST-cached equivalent.
- `remote/` -- REST-downloaded `.gpkg` cache via `ensure_layers()`, gitignored.
  Delete a file to force a fresh download; there is no separate versioning
  scheme beyond "delete and re-fetch."
- `processed/` -- intermediate outputs, gitignored.

`projects/<name>/output/` holds final deliverables and is tracked by default.

## Quarto site

Single root-level website (`_quarto.yml`) aggregates every project's
`index.qmd` as a page, styled via the `WFRCAnalytics/wfrc-brand` extension
(`_extensions/WFRCAnalytics/wfrc-brand/`). Renders to `docs/` (tracked in
git, not gitignored) so GitHub Pages can serve it directly from `main` with
no CI/build step -- enable it in repo Settings -> Pages -> Source: `main`
branch, `/docs` folder. Run `uv run quarto render` and commit `docs/` before
pushing to publish. `freeze: auto` caches execution output; `_freeze/` stays
gitignored for now since renders happen locally with live data access, not
in CI -- see `WFRCAnalytics/GIS-RTP-Phasing-Criteria` if a CI-based rebuild
(needing committed `_freeze/`) is ever needed instead.
