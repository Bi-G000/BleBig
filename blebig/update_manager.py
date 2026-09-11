from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from . import __version__
from .paths import data_dir, install_dir, update_dir
from .update_package import inspect_package

LOG = logging.getLogger("blebig.update")
def offer_pending_update():
    packages = sorted(update_dir().glob("*.zip"))
    if not packages: return False
    package = packages[-1]
    try: manifest = inspect_package(package, __version__)
    except Exception as exc:
        LOG.exception("Gói cập nhật bị từ chối")
        package.rename(package.with_suffix(package.suffix + ".rejected"))
        QMessageBox.critical(None, "BleBig Update", f"Gói cập nhật không hợp lệ và đã bị từ chối:\n{exc}")
        return False
    changes = "\n• ".join(manifest.get("changes", ["Cải thiện BleBig"]))
    QMessageBox.information(None, "BleBig Update", f"Tìm thấy BleBig {manifest['version']}\n\nThay đổi:\n• {changes}\n\nBleBig sẽ cập nhật và tự mở lại.")
    return launch_package(package)


def launch_package(package):
    try:
        inspect_package(Path(package), __version__)
    except Exception as exc:
        QMessageBox.critical(None, "BleBig Update", f"Không thể áp dụng gói cập nhật:\n{exc}")
        return False
    updater = install_dir() / "BleBigUpdater.exe"
    if not updater.exists():
        QMessageBox.critical(None, "BleBig Update", "Thiếu BleBigUpdater.exe. Gói cập nhật chưa được áp dụng.")
        return False
    subprocess.Popen([str(updater), "--package", str(package), "--install-dir", str(install_dir()), "--pid", str(__import__('os').getpid())], close_fds=True)
    return True


def consume_update_result():
    result = data_dir() / "update-result.json"
    if not result.exists(): return None
    try:
        data = json.loads(result.read_text(encoding="utf-8")); result.unlink(missing_ok=True)
        return data.get("message", "BleBig đã cập nhật thành công.")
    except Exception:
        return None
