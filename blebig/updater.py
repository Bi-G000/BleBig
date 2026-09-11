from __future__ import annotations

import argparse
import json
import os
import shutil
import time
import zipfile
from pathlib import Path

from .update_package import inspect_package, safe_relative


def wait_for_pid(pid, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try: os.kill(pid, 0)
        except OSError: return
        time.sleep(.3)
    raise TimeoutError("BleBig không đóng sau 60 giây")


def apply_update(package, install, result_file):
    staging = install / ".update-staging"; backup = install / ".update-backup"
    manifest = {"files": []}
    shutil.rmtree(staging, ignore_errors=True); shutil.rmtree(backup, ignore_errors=True)
    staging.mkdir(); backup.mkdir()
    try:
        manifest = inspect_package(package)
        with zipfile.ZipFile(package) as archive:
            files = manifest["files"]
            for item in files:
                relative = safe_relative(item["path"]); raw = archive.read("payload/" + relative.as_posix())
                target = staging / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        changed = []
        for item in files:
            relative = safe_relative(item["path"]); destination = install / relative
            if destination.exists():
                saved = backup / relative; saved.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(destination, saved)
            destination.parent.mkdir(parents=True, exist_ok=True); os.replace(staging / relative, destination); changed.append(relative)
        package.unlink(); shutil.rmtree(staging, ignore_errors=True); shutil.rmtree(backup, ignore_errors=True)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(json.dumps({"message": f"Đã cập nhật BleBig {manifest['version']} thành công."}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        for item in manifest.get("files", []):
            relative = safe_relative(item["path"]); saved = backup / relative; target = install / relative
            if saved.exists():
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(saved, target)
            elif target.exists():
                target.unlink()
        raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--package",required=True);parser.add_argument("--install-dir",required=True);parser.add_argument("--pid",required=True,type=int);args=parser.parse_args()
    install=Path(args.install_dir).resolve(); package=Path(args.package).resolve(); wait_for_pid(args.pid)
    local=Path(os.environ.get("LOCALAPPDATA",Path.home()))/"BleBig"/"update-result.json"
    try:
        apply_update(package,install,local)
        code=0
    except Exception as exc:
        local.parent.mkdir(parents=True,exist_ok=True)
        local.write_text(json.dumps({"message":f"Cập nhật thất bại, BleBig đã phục hồi bản cũ.\n{exc}"},ensure_ascii=False),encoding="utf-8")
        code=1
    os.startfile(install/"BleBig.exe")
    return code


if __name__ == "__main__": raise SystemExit(main())
