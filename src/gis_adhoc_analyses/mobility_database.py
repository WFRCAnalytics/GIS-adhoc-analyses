"""Minimal client for the Mobility Database catalog API (GTFS feed archive).

Talks to https://api.mobilitydatabase.org directly via ``requests``.
Authentication: put ``MOBILITY_DATABASE_REFRESH_TOKEN`` in ``.env``; a
short-lived access token is exchanged for it on demand.

Typical use::

    from gis_adhoc_analyses.mobility_database import list_datasets, download_dataset

    datasets = list_datasets("mdb-170")           # every archived snapshot of a feed
    path = download_dataset(datasets[-1], "_data/remote/gtfs")   # cached .zip
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://api.mobilitydatabase.org/v1"
TIMEOUT = 120


def get_access_token() -> str:
    """Exchange the refresh token in ``.env`` for a short-lived access token."""
    load_dotenv()
    refresh = os.environ.get("MOBILITY_DATABASE_REFRESH_TOKEN")
    if not refresh:
        raise RuntimeError("MOBILITY_DATABASE_REFRESH_TOKEN is not set (see .env.example).")
    r = requests.post(f"{API_URL}/tokens", json={"refresh_token": refresh}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["access_token"]


def list_datasets(
    feed_id: str, cache: str | Path | None = None, refresh: bool = False
) -> list[dict]:
    """Return every archived dataset (snapshot) of a GTFS feed, oldest first.

    If ``cache`` is given the listing is stored there as JSON and reused until
    ``refresh=True``, so reruns work offline and are reproducible.
    """
    cache = Path(cache) if cache else None
    if cache and cache.exists() and not refresh:
        return json.loads(cache.read_text())

    headers = {"Authorization": f"Bearer {get_access_token()}"}
    datasets: list[dict] = []
    offset, limit = 0, 100
    while True:
        r = requests.get(
            f"{API_URL}/gtfs_feeds/{feed_id}/datasets",
            headers=headers,
            params={"limit": limit, "offset": offset},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        page = r.json()
        datasets.extend(page)
        if len(page) < limit:
            break
        offset += limit
    datasets.sort(key=lambda d: d["downloaded_at"])

    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(datasets, indent=1))
    return datasets


def download_dataset(dataset: dict, dest_dir: str | Path, force: bool = False) -> Path:
    """Download one dataset's GTFS .zip into ``dest_dir`` (skipped if already cached)."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{dataset['id']}.zip"
    if path.exists() and not force:
        return path
    tmp = path.with_suffix(".part")
    with requests.get(dataset["hosted_url"], stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.replace(path)
    return path
