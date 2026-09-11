from __future__ import annotations

import importlib.util
import os
import platform
import shutil
from dataclasses import dataclass


@dataclass
class DiagnosticResult:
    ok: bool
    lines: list[str]


def run_diagnostics() -> DiagnosticResult:
    lines = [
        f"Hệ điều hành: {platform.platform()}",
        f"Kiến trúc: {platform.machine()}",
        f"CPU: {os.cpu_count() or 'Không xác định'} luồng",
    ]
    free_gb = shutil.disk_usage(os.environ.get("LOCALAPPDATA", ".")).free / 1024**3
    lines.append(f"Dung lượng trống: {free_gb:.1f} GB")
    missing = []
    for module in ("PIL", "numpy", "cv2", "PySide6"):
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    try:
        import torch

        lines.append(f"PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            lines.append(f"GPU AI: {torch.cuda.get_device_name(0)} (CUDA)")
        else:
            lines.append("GPU AI: Không có CUDA, AI sẽ dùng CPU")
    except Exception as exc:
        missing.append(f"torch ({exc})")
    if free_gb < 3:
        lines.append("CẢNH BÁO: Nên còn ít nhất 3 GB để tải model và xử lý ảnh.")
    if missing:
        lines.append("THIẾU: " + ", ".join(missing))
    else:
        lines.append("Các thành phần bắt buộc: Đầy đủ")
    return DiagnosticResult(not missing and free_gb >= 1, lines)

