"""
Utility functions for downloading ArcGIS FeatureServer/MapServer layers.

Uses the ArcGIS REST API directly via `requests` -- no arcgis SDK required.

Ordering and duplication safety
--------------------------------
Query-layer / SQL-view / joined services can regenerate OBJECTIDs
non-deterministically between requests. Fetching an ID list and then
fetching each batch by ID (the standard approach) can silently duplicate,
drop, or reorder rows if those two calls don't see the same ID assignment.
``fetch_feature_layer`` guards against this by:

- sorting the fetched ID list before batching, so batching is deterministic
  and reproducible run-to-run instead of relying on server-returned order
- retrying (once, with backoff) any batch that returns fewer features than
  IDs requested, instead of silently accepting a partial response
- deduplicating the final result on the service's actual object-ID field
  after concatenation, warning if duplicates were found
- verifying the final unique row count against the original ID count and
  raising if rows were lost (a mismatch here means the service disagreed
  with itself between the two calls -- silently returning partial data
  would be worse than a loud failure)

For layers known to have unstable OBJECTIDs (flag with ``pagination: offset``
in sources.yml), pass ``pagination="offset"`` and a genuinely stable
``order_by`` field (never OBJECTID for these layers) to fall back to
resultOffset-based pagination instead. That path increments by the actual
record count returned each page (never an assumed page size) and stops when
the server reports ``exceededTransferLimit: false`` -- the same final
dedupe/verify steps apply regardless of which path was used.

Authentication
---------------
Public layers (e.g. OpenSGID) work without a token.

For private/secured layers, set credentials in a ``.env`` file at the repo
root::

    ARCGIS_USERNAME=your_username
    ARCGIS_PASSWORD=your_password
    ARCGIS_PORTAL_URL=https://your-portal.com  # optional, defaults to ArcGIS Online

Then call ``generate_token()`` with no arguments and pass the result to
``fetch_feature_layer``::

    token = generate_token()
    gdf = fetch_feature_layer(service_url, token=token)
"""

import io
import os
import time
import warnings
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


def generate_token(
    username: str | None = None,
    password: str | None = None,
    portal_url: str | None = None,
    expiration: int = 60,
) -> str:
    """
    Generate a short-lived ArcGIS token for accessing secured services.

    Reads credentials from environment variables by default (set in ``.env``):
    ``ARCGIS_USERNAME``, ``ARCGIS_PASSWORD``, ``ARCGIS_PORTAL_URL``. Any
    argument passed explicitly takes precedence over the env var.

    Parameters
    ----------
    username : str, optional
        ArcGIS / Portal username. Falls back to ``ARCGIS_USERNAME`` env var.
    password : str, optional
        ArcGIS / Portal password. Falls back to ``ARCGIS_PASSWORD`` env var.
    portal_url : str, optional
        Base URL of the ArcGIS portal. Falls back to ``ARCGIS_PORTAL_URL``
        env var, then defaults to ``https://www.arcgis.com``.
    expiration : int, optional
        Token lifetime in minutes. Default is 60.

    Returns
    -------
    str
        A token string to pass to ``fetch_feature_layer``.

    Raises
    ------
    EnvironmentError
        If username or password cannot be resolved from arguments or env vars.
    PermissionError
        If the portal rejects the credentials.
    """
    username = username or os.getenv("ARCGIS_USERNAME")
    password = password or os.getenv("ARCGIS_PASSWORD")
    portal_url = portal_url or os.getenv("ARCGIS_PORTAL_URL", "https://www.arcgis.com")

    if not username or not password:
        raise OSError(
            "ArcGIS credentials not found. Set ARCGIS_USERNAME and ARCGIS_PASSWORD "
            "in a .env file at the repo root, or pass them explicitly."
        )

    token_url = portal_url.rstrip("/") + "/sharing/rest/generateToken"
    payload = {
        "username": username,
        "password": password,
        "client": "referer",
        "referer": "https://services1.arcgis.com",
        "expiration": expiration,
        "f": "json",
    }
    response = requests.post(token_url, data=payload, timeout=30)
    response.raise_for_status()

    result = response.json()
    if "error" in result:
        raise PermissionError(
            f"Token generation failed: {result['error'].get('message', result['error'])}"
        )
    return result["token"]


def _check_error(payload: dict, service_url: str) -> None:
    """Raise a meaningful exception if the ArcGIS response contains an error."""
    if "error" in payload:
        code = payload["error"].get("code")
        message = payload["error"].get("message", str(payload["error"]))
        if code in (499, 498):  # 499 = token required, 498 = token invalid/expired
            raise PermissionError(
                f"Authentication required for {service_url}. "
                f"Call generate_token() and pass the result as token=. "
                f"Server message: {message}"
            )
        raise RuntimeError(f"ArcGIS service error ({code}): {message}")


def _service_info(base_url: str, auth: dict, headers: dict) -> dict:
    resp = requests.get(base_url, params={"f": "json", **auth}, headers=headers, timeout=30)
    resp.raise_for_status()
    info = resp.json()
    _check_error(info, base_url)
    return info


def _fetch_batch_geojson(
    query_url: str,
    object_ids: list[int],
    out_fields: str,
    out_sr: int,
    auth: dict,
    headers: dict,
    retries: int = 1,
) -> gpd.GeoDataFrame:
    """POST one objectId batch, returning it as a GeoDataFrame; retries short responses once."""
    last_gdf: gpd.GeoDataFrame | None = None
    for attempt in range(retries + 1):
        resp = requests.post(
            query_url,
            data={
                "objectIds": ",".join(str(i) for i in object_ids),
                "outFields": out_fields,
                "returnGeometry": "true",
                "outSR": out_sr,
                "f": "geojson",
                **auth,
            },
            headers=headers,
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
        _check_error(payload, query_url)

        chunk = gpd.read_file(io.BytesIO(resp.content))
        if len(chunk) >= len(object_ids):
            return chunk

        last_gdf = chunk
        if attempt < retries:
            print(
                f"    Batch returned {len(chunk)}/{len(object_ids)} features -- "
                f"retrying in {2**attempt}s ..."
            )
            time.sleep(2**attempt)

    return last_gdf if last_gdf is not None else gpd.GeoDataFrame()


def _fetch_by_object_ids(
    query_url: str,
    all_ids: list[int],
    max_count: int,
    out_fields: str,
    out_sr: int,
    auth: dict,
    headers: dict,
) -> list[gpd.GeoDataFrame]:
    """Sort ids for deterministic batching, then batch-fetch by objectId (POST avoids long URIs)."""
    all_ids = sorted(all_ids)
    gdfs = []
    for batch_start in range(0, len(all_ids), max_count):
        batch_ids = all_ids[batch_start : batch_start + max_count]
        batch_end = batch_start + len(batch_ids)
        print(f"  Fetching features {batch_start + 1}-{batch_end} of {len(all_ids)} ...")
        chunk = _fetch_batch_geojson(query_url, batch_ids, out_fields, out_sr, auth, headers)
        if not chunk.empty:
            gdfs.append(chunk)
    return gdfs


def _fetch_by_offset(
    query_url: str,
    order_by: str,
    max_count: int,
    where: str,
    out_fields: str,
    out_sr: int,
    auth: dict,
    headers: dict,
) -> list[gpd.GeoDataFrame]:
    """
    Fallback pagination for layers with unstable OBJECTIDs (query layers / views).

    Pages by resultOffset with an explicit, genuinely stable orderByFields
    (never OBJECTID for these layers), advancing by the actual record count
    returned each page and stopping on exceededTransferLimit: false.
    """
    gdfs = []
    offset = 0
    while True:
        resp = requests.post(
            query_url,
            data={
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "true",
                "outSR": out_sr,
                "orderByFields": order_by,
                "resultOffset": offset,
                "resultRecordCount": max_count,
                "f": "geojson",
                **auth,
            },
            headers=headers,
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
        _check_error(payload, query_url)

        chunk = gpd.read_file(io.BytesIO(resp.content))
        print(f"  Fetched {len(chunk)} features at offset {offset} ...")
        if not chunk.empty:
            gdfs.append(chunk)

        exceeded = payload.get("exceededTransferLimit", False)
        offset += len(chunk)
        if not exceeded or chunk.empty:
            break
    return gdfs


def fetch_feature_layer(
    service_url: str,
    out_sr: int = 4326,
    where: str = "1=1",
    out_fields: str = "*",
    token: str | None = None,
    pagination: str = "objectid",
    order_by: str | None = None,
) -> gpd.GeoDataFrame:
    """
    Fetch an ArcGIS FeatureServer layer and return as a GeoDataFrame.

    Parameters
    ----------
    service_url : str
        Full URL to the ArcGIS FeatureServer layer endpoint, ending with
        the layer index (e.g. ``https://services.arcgis.com/.../FeatureServer/0``).
    out_sr : int, optional
        Output spatial reference EPSG code. Default is 4326 (WGS84).
    where : str, optional
        SQL where clause to filter features. Default ``'1=1'`` returns all.
    out_fields : str, optional
        Comma-separated field names to return. Default ``'*'`` returns all.
    token : str, optional
        ArcGIS token for accessing secured services. Generate one with
        ``generate_token()``. Leave as ``None`` for public layers.
    pagination : {"objectid", "offset"}, optional
        ``"objectid"`` (default) fetches all matching objectIds up front and
        batches by ID -- fast and safe for ordinary services. ``"offset"``
        is a fallback for query-layer/joined services with non-deterministic
        OBJECTIDs; requires ``order_by``.
    order_by : str, optional
        Stable sort field, required when ``pagination="offset"``.

    Returns
    -------
    geopandas.GeoDataFrame
        All fetched features as a GeoDataFrame with CRS set to ``out_sr``.
        Deduplicated on the service's object-ID field.

    Raises
    ------
    PermissionError
        If the service requires a token and none was provided, or if the
        token is invalid/expired.
    ValueError
        If the service returns no features, or if fewer unique rows were
        returned than the service reported matching -- rather than silently
        returning partial data.
    """
    if pagination == "offset" and not order_by:
        raise ValueError('pagination="offset" requires an order_by field')

    base_url = service_url.rstrip("/")
    query_url = base_url + "/query"
    auth = {"token": token} if token else {}
    headers = {"Referer": "https://services1.arcgis.com"} if token else {}

    info = _service_info(base_url, auth, headers)
    max_count = int(info.get("maxRecordCount", 1000))
    id_field = info.get("objectIdField", "OBJECTID")
    print(f"Service maxRecordCount: {max_count}, objectIdField: {id_field}")

    if pagination == "offset":
        gdfs = _fetch_by_offset(
            query_url, order_by, max_count, where, out_fields, out_sr, auth, headers
        )
        expected_count = None
    else:
        id_resp = requests.get(
            query_url,
            params={"where": where, "returnIdsOnly": "true", "f": "json", **auth},
            headers=headers,
            timeout=60,
        )
        id_resp.raise_for_status()
        id_payload = id_resp.json()
        _check_error(id_payload, service_url)

        all_ids = id_payload.get("objectIds") or []
        if not all_ids:
            raise ValueError(f"No features matched where='{where}' on {service_url}")
        expected_count = len(all_ids)
        print(f"Total features to fetch: {expected_count}")

        gdfs = _fetch_by_object_ids(
            query_url, all_ids, max_count, out_fields, out_sr, auth, headers
        )

    if not gdfs:
        raise ValueError(f"No features returned from {service_url}")

    gdf = gpd.GeoDataFrame(
        pd.concat(gdfs, ignore_index=True), geometry="geometry", crs=f"EPSG:{out_sr}"
    )

    if id_field in gdf.columns:
        before = len(gdf)
        gdf = gdf.drop_duplicates(subset=[id_field]).reset_index(drop=True)
        n_dupes = before - len(gdf)
        if n_dupes:
            warnings.warn(
                f"Dropped {n_dupes} duplicate row(s) on '{id_field}' -- the service "
                f"returned the same feature more than once (common for query-layer/"
                f"joined services). Consider pagination='offset' with a stable order_by "
                f"for this layer.",
                UserWarning,
                stacklevel=2,
            )

    if expected_count is not None and len(gdf) < expected_count:
        raise ValueError(
            f"Expected {expected_count} unique features but only {len(gdf)} were returned "
            f"after dedup. The service likely disagreed with itself between the ID-list "
            f"and batch-fetch calls -- retry, or use pagination='offset' with a stable "
            f"order_by field for this layer."
        )

    print(f"Done. Total features fetched: {len(gdf)}")
    return gdf


_STALE_WARNING_DAYS = 365  # warn if cache is older than this


def _print_cache_age(cache_path: Path) -> None:
    """Print cache age; warn if stale."""
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
    age_days = (datetime.now(tz=UTC) - mtime).days
    if age_days > _STALE_WARNING_DAYS:
        warnings.warn(
            f"Cache file is {age_days} days old ({cache_path.name}). "
            f"Re-run with force=True to fetch the latest version.",
            UserWarning,
            stacklevel=3,
        )
    else:
        print(f"Using cached file ({age_days}d old): {cache_path.name}")


def download_layer(
    cache_path: Path | str,
    service_url: str,
    force: bool = False,
    token: str | None = None,
    **fetch_kwargs,
) -> None:
    """
    Download an ArcGIS FeatureServer layer to a local GeoPackage cache file.

    Only downloads if the cache file is absent or ``force=True``. If the
    cache exists but is older than one year, a warning is printed suggesting
    a forced refresh -- the existing file is still used.

    Parameters
    ----------
    cache_path : Path or str
        Local ``.gpkg`` file to write to. Parent directories are created automatically.
    service_url : str
        ArcGIS FeatureServer layer URL passed to ``fetch_feature_layer``.
    force : bool, optional
        Re-download even if a local cache exists. Default ``False``.
    token : str, optional
        ArcGIS token for secured services. See ``generate_token()``.
    **fetch_kwargs
        Extra keyword arguments forwarded to ``fetch_feature_layer``
        (e.g. ``where``, ``out_fields``, ``out_sr``, ``pagination``, ``order_by``).
    """
    cache_path = Path(cache_path)

    if cache_path.exists() and not force:
        _print_cache_age(cache_path)
        return

    if force and cache_path.exists():
        print(f"Force re-download: {cache_path.name}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    gdf = fetch_feature_layer(service_url, token=token, **fetch_kwargs)
    gdf.to_file(cache_path, driver="GPKG")
    print(f"Saved to cache: {cache_path}")


def download_zip_layer(
    cache_path: Path | str,
    url: str,
    layer_name: str | None = None,
    gdb_name: str | None = None,
    where: str | None = None,
    force: bool = False,
) -> None:
    """
    Download a ZIP archive and save one spatial layer from it to a GeoPackage.

    The ZIP is downloaded to ``cache_path.with_suffix('.zip')`` and deleted
    once the ``.gpkg`` has been built. If a ZIP from an interrupted previous
    run is still on disk, it's reused instead of re-downloaded.

    Parameters
    ----------
    cache_path : Path or str
        Local ``.gpkg`` to write. Parent dirs are created automatically.
    url : str
        Direct-download URL for the ZIP file.
    layer_name : str, optional
        ``.shp`` filename inside the ZIP, or GDB layer name when ``gdb_name``
        is given. Defaults to the first ``.shp`` found for shapefiles.
    gdb_name : str, optional
        ``.gdb`` directory name inside the ZIP (e.g. ``"HPMS2024.gdb"``).
    where : str, optional
        OGR SQL WHERE clause applied when reading the layer, e.g.
        ``"county_id IN (3, 11, 35, 57)"``.
    force : bool, optional
        Re-download the ZIP and rebuild the ``.gpkg``. Default ``False``.
    """
    cache_path = Path(cache_path)

    if cache_path.exists() and not force:
        _print_cache_age(cache_path)
        return

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path = cache_path.with_suffix(".zip")

    if not zip_path.exists() or force:
        print(f"Downloading ZIP: {url}")
        resp = requests.get(url, timeout=600, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65_536):
                fh.write(chunk)
        print(f"Downloaded {zip_path.stat().st_size / 1e6:.1f} MB -> {zip_path.name}")
    else:
        print(f"Using existing ZIP ({zip_path.stat().st_size / 1e6:.1f} MB): {zip_path.name}")

    vsizip_base = f"/vsizip/{zip_path.as_posix()}"
    read_kwargs: dict = {}
    if where:
        read_kwargs["where"] = where

    if gdb_name:
        read_path = f"{vsizip_base}/{gdb_name}"
        if layer_name:
            read_kwargs["layer"] = layer_name
        print(f"Reading GDB layer via /vsizip/: {gdb_name}/{layer_name or '(default)'}")
    else:
        with zipfile.ZipFile(zip_path) as zf:
            shp_names = [n for n in zf.namelist() if n.lower().endswith(".shp")]
        if not shp_names:
            raise ValueError(f"No .shp or gdb_name found in {zip_path}")
        target = layer_name if layer_name else shp_names[0]
        if target not in shp_names:
            raise ValueError(f"Layer {target!r} not in ZIP. Available: {shp_names}")
        read_path = f"{vsizip_base}/{target}"
        print(f"Reading shapefile via /vsizip/: {target}")

    gdf = gpd.read_file(read_path, **read_kwargs)
    gdf.to_file(cache_path, driver="GPKG")
    print(f"Saved to cache: {cache_path} ({len(gdf):,} features)")

    zip_path.unlink()
    print(f"Deleted ZIP: {zip_path.name}")
