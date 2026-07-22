"""
Layer cache manager for ArcGIS REST data sources.

Each project defines its own ``sources.yml`` (not a repo-global registry --
projects in this repo are unrelated ad hoc analyses). Notebooks/scripts call
``ensure_layers()`` to verify caches exist -- downloading missing files and
printing the age of files that are already cached -- before reading with
``gpd.read_file(L["key"])``.

Cache paths in sources.yml are relative to the sources.yml file itself (not
the repo root or the current working directory), so a project folder stays
self-contained and portable when copied from projects/_template.

Usage
-----
    from gis_tools.layer_cache import ensure_layers

    L = ensure_layers(["bikeways", "at_point_projects"])

    bikeways = gpd.read_file(L["bikeways"])
    points = gpd.read_file(L["at_point_projects"])

To force re-download of specific layers (e.g. after a URL change)::

    L = ensure_layers([...], force=["at_point_projects"])

To force re-download of every layer requested::

    L = ensure_layers([...], force=True)

Layers marked ``access: private`` in sources.yml need ARCGIS_USERNAME /
ARCGIS_PASSWORD in .env -- ensure_layers() generates the token automatically.
"""

from pathlib import Path

import yaml

from gis_tools.arcgis_utils import download_layer, download_zip_layer, generate_token


def _load_sources(sources_path: Path) -> dict:
    with open(sources_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["layers"]


def ensure_layers(
    keys: list[str],
    sources_path: str | Path = "sources.yml",
    force: bool | list[str] = False,
    token: str | None = None,
) -> dict[str, Path]:
    """
    Ensure cached .gpkg files exist for the requested layer keys.

    For each key, prints the cache age if the file exists or downloads it
    from the service URL defined in sources.yml. Returns a dict mapping each
    key to its resolved local Path for use with gpd.read_file().

    Layers marked ``access: private`` in sources.yml require authentication.
    If no ``token`` is passed, one is generated automatically via
    ``generate_token()`` the first time a private layer needs downloading.
    The same token is reused for all private layers in the same call.
    Credentials must be set in ``.env`` at the repo root.

    Parameters
    ----------
    keys : list[str]
        Layer keys defined in sources.yml (e.g. ["bikeways", "at_point_projects"]).
    sources_path : str or Path, optional
        Path to this project's sources.yml. Defaults to "sources.yml" in the
        current working directory (the project folder, when Quarto's
        default per-file execute-dir is used). Cache paths inside sources.yml
        are resolved relative to this file's parent directory.
    force : bool or list[str], optional
        - False (default) -- use the existing cache file.
        - True -- re-download every layer in *keys* unconditionally.
        - list[str] -- re-download only the named keys; use the cache for others.
    token : str, optional
        ArcGIS token for secured services. If omitted, one is generated
        automatically for layers marked ``access: private`` in sources.yml.

    Returns
    -------
    dict[str, Path]
        {layer_key: Path} for every key requested. Pass directly to gpd.read_file().

    Raises
    ------
    KeyError
        If a requested key is not defined in sources.yml.
    """
    sources_path = Path(sources_path)
    base_dir = sources_path.parent
    sources = _load_sources(sources_path)

    paths: dict[str, Path] = {}
    auto_token: str | None = token  # generated once on first private layer; reused

    for key in keys:
        if key not in sources:
            available = ", ".join(sorted(sources))
            raise KeyError(f"Unknown layer key {key!r}. Available keys in sources.yml:\n  {available}")

        entry = sources[key]
        cache_path = base_dir / entry["cache"]
        url = entry["url"]
        layer_type = entry.get("type", "feature_server")
        is_private = entry.get("access") == "private"

        should_force = force is True or (isinstance(force, list) and key in force)

        if should_force or not cache_path.exists():
            if is_private and auto_token is None:
                print(f"Layer '{key}' is private -- generating token from .env credentials")
                auto_token = generate_token()

        layer_token = auto_token if is_private else None

        if layer_type == "zip_download":
            download_zip_layer(
                cache_path,
                url,
                layer_name=entry.get("layer_name"),
                gdb_name=entry.get("gdb_name"),
                where=entry.get("where"),
                force=should_force,
            )
        else:
            fetch_kwargs = {}
            if "where" in entry:
                fetch_kwargs["where"] = entry["where"]
            if "pagination" in entry:
                fetch_kwargs["pagination"] = entry["pagination"]
            if "order_by" in entry:
                fetch_kwargs["order_by"] = entry["order_by"]
            download_layer(cache_path, url, force=should_force, token=layer_token, **fetch_kwargs)

        paths[key] = cache_path

    return paths
