import json
import re
import xml.etree.ElementTree as ET
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

REMOTE_DIR = "ESO-Builds"
_DAV_NS = {"d": "DAV:"}


class NextcloudSyncError(Exception):
    pass


class NextcloudSync:
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self._username = username
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(username, password)
        self._session.verify = verify_ssl

    def _dav_url(self, path: str = "") -> str:
        base = f"{self.base_url}/remote.php/dav/files/{self._username}/{REMOTE_DIR}"
        return f"{base}/{path}" if path else base + "/"

    def test_connection(self) -> None:
        resp = self._session.request(
            "PROPFIND",
            f"{self.base_url}/remote.php/dav/files/{self._username}/",
            headers={"Depth": "0"},
        )
        if not resp.ok:
            raise NextcloudSyncError(f"Connection failed: HTTP {resp.status_code}")

    def ensure_directory(self) -> None:
        resp = self._session.request("MKCOL", self._dav_url())
        if resp.status_code not in (201, 405):
            raise NextcloudSyncError(
                f"Could not create {REMOTE_DIR}/: HTTP {resp.status_code}"
            )

    def list_remote_builds(self) -> list[str]:
        """Returns list of .json filenames in ESO-Builds/ via PROPFIND."""
        resp = self._session.request(
            "PROPFIND",
            self._dav_url(),
            headers={"Depth": "1"},
        )
        if resp.status_code == 404:
            return []
        if not resp.ok:
            raise NextcloudSyncError(f"PROPFIND failed: HTTP {resp.status_code}")

        root = ET.fromstring(resp.text)
        filenames = []
        for response_el in root.findall(".//d:response", _DAV_NS):
            href = response_el.findtext("d:href", namespaces=_DAV_NS) or ""
            name = href.rstrip("/").split("/")[-1]
            if name.endswith(".json"):
                filenames.append(name)
        return filenames

    def upload_build(self, slug: str, data: dict) -> None:
        resp = self._session.put(
            self._dav_url(f"{slug}.json"),
            data=json.dumps(data, indent=2),
            headers={"Content-Type": "application/json"},
        )
        if not resp.ok:
            raise NextcloudSyncError(f"Upload {slug}: HTTP {resp.status_code}")

    def download_build(self, filename: str) -> dict:
        resp = self._session.get(self._dav_url(filename))
        if not resp.ok:
            raise NextcloudSyncError(f"Download {filename}: HTTP {resp.status_code}")
        return resp.json()


def _make_slug(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"[\s]+", "_", s) or "build"


def sync_all(syncer: NextcloudSync) -> tuple[int, int, list[str]]:
    """Two-way sync: upload all local builds; download remote-only or newer builds.

    Returns (uploaded, downloaded, errors).
    """
    import eso_build_manager.storage.database as db
    from eso_build_manager.exporter import export_build_dict, import_build_dict

    errors: list[str] = []
    uploaded = 0
    downloaded = 0

    syncer.ensure_directory()

    local_meta = db.list_builds_meta()  # (id, name, role, eso_class, content)

    # Build slug→(build_id, updated_at) map, deduplicating slugs
    slug_map: dict[str, tuple[int, str]] = {}
    for build_id, name, _, _, _ in local_meta:
        slug = _make_slug(name)
        base = slug
        i = 2
        while slug in slug_map:
            slug = f"{base}_{i}"
            i += 1
        build = db.get_build(build_id)
        slug_map[slug] = (build_id, build.updated_at if build else "")

    # Upload all local builds
    uploaded_files: set[str] = set()
    for slug, (build_id, updated_at) in slug_map.items():
        try:
            data = export_build_dict(build_id)
            data["_sync_updated_at"] = updated_at
            syncer.upload_build(slug, data)
            uploaded_files.add(f"{slug}.json")
            uploaded += 1
        except Exception as e:
            errors.append(f"Upload '{slug}': {e}")

    # Download remote builds not present locally (or newer than local)
    try:
        remote_files = syncer.list_remote_builds()
    except NextcloudSyncError as e:
        errors.append(f"List remote: {e}")
        return uploaded, downloaded, errors

    local_names_lower = {name.lower() for _, name, _, _, _ in local_meta}

    for filename in remote_files:
        if filename in uploaded_files:
            continue
        try:
            data = syncer.download_build(filename)
            remote_name = data.get("name", "")
            if not remote_name:
                continue

            if remote_name.lower() not in local_names_lower:
                import_build_dict(data)
                downloaded += 1
            else:
                # Same name exists locally — import only if remote is newer
                remote_ts = data.get("_sync_updated_at", "")
                match = next(
                    (
                        (bid, ts)
                        for slug, (bid, ts) in slug_map.items()
                        if _make_slug(remote_name) == slug
                    ),
                    None,
                )
                if match and remote_ts > match[1]:
                    import_build_dict(data)
                    downloaded += 1
        except Exception as e:
            errors.append(f"Download '{filename}': {e}")

    return uploaded, downloaded, errors
