from __future__ import annotations

import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .paths import resource_path, update_dir
from .update_package import version_tuple

LOG = logging.getLogger("blebig.online_update")


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    changes: str
    download_url: str
    file_name: str


def _repository():
    try:
        data = json.loads(resource_path("assets/update-channel.json").read_text(encoding="utf-8"))
        repo = str(data.get("repository", "")).strip()
        if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) and "__" not in repo:
            return repo
    except Exception:
        LOG.debug("Chưa cấu hình GitHub update", exc_info=True)
    return None


def _enable_windows_trust():
    try:
        import truststore
        truststore.inject_into_ssl()
    except Exception:
        LOG.debug("Không nạp được Windows trust store", exc_info=True)


def check_latest(timeout=8):
    repo = _repository()
    if not repo: return None
    _enable_windows_trust()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers={"Accept":"application/vnd.github+json", "User-Agent":f"BleBig/{__version__}"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        release = json.loads(response.read().decode("utf-8"))
    version = str(release.get("tag_name", "")).lstrip("vV")
    if version_tuple(version) <= version_tuple(__version__): return None
    assets = release.get("assets", [])
    asset = next((x for x in assets if re.fullmatch(r"BleBig-Update-v?.*\.zip", x.get("name", ""), re.I)), None)
    if not asset: raise RuntimeError("Phiên bản mới chưa có gói BleBig-Update ZIP")
    return ReleaseInfo(version, (release.get("body") or "Cải thiện BleBig").strip(),
        asset["browser_download_url"], asset["name"])


def download_release(info: ReleaseInfo, progress=None):
    _enable_windows_trust(); destination = update_dir() / info.file_name
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(info.download_url, headers={"User-Agent":f"BleBig/{__version__}"})
    with urllib.request.urlopen(request, timeout=30) as response, temporary.open("wb") as output:
        total = int(response.headers.get("Content-Length", 0)); received = 0
        while True:
            block = response.read(1024 * 1024)
            if not block: break
            output.write(block); received += len(block)
            if progress: progress(received, total)
    temporary.replace(destination)
    return destination

