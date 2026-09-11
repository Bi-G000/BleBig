from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


MANIFEST = "blebig-update.json"


def version_tuple(value):
    try: return tuple(int(part) for part in value.split("."))
    except Exception: return (0,)


def safe_relative(value):
    path = PurePosixPath(value.replace("\\", "/"))
    reserved = {"update", ".update-staging", ".update-backup"}
    if path.is_absolute() or ".." in path.parts or not path.parts or ":" in path.parts[0] or path.parts[0].lower() in reserved:
        raise ValueError(f"Đường dẫn nguy hiểm: {value}")
    return Path(*path.parts)


def inspect_package(package: Path, current_version: str | None = None):
    with zipfile.ZipFile(package) as archive:
        if MANIFEST not in archive.namelist(): raise ValueError("Thiếu blebig-update.json")
        manifest = json.loads(archive.read(MANIFEST).decode("utf-8"))
        if manifest.get("app_id") != "com.thienha.blebig": raise ValueError("Gói cập nhật không thuộc BleBig")
        if current_version and version_tuple(manifest.get("version", "0")) <= version_tuple(current_version):
            raise ValueError("Phiên bản cập nhật không mới hơn bản hiện tại")
        files = manifest.get("files", [])
        if not files: raise ValueError("Danh sách cập nhật trống")
        for item in files:
            relative = safe_relative(item["path"])
            if relative.name.lower() == "blebigupdater.exe": raise ValueError("Không thể tự ghi đè BleBigUpdater.exe")
            archive_name = "payload/" + relative.as_posix()
            if archive_name not in archive.namelist(): raise ValueError(f"Thiếu file: {relative}")
            if hashlib.sha256(archive.read(archive_name)).hexdigest() != item["sha256"].lower():
                raise ValueError(f"Sai SHA-256: {relative}")
        return manifest
