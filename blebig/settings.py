from __future__ import annotations

import json

from .paths import data_dir


def load_custom_sizes():
    path = data_dir() / "custom-sizes.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): (float(v[0]), float(v[1])) for k, v in raw.items()}
    except Exception:
        return {}


def save_custom_sizes(sizes):
    path = data_dir() / "custom-sizes.json"
    path.write_text(json.dumps(sizes, ensure_ascii=False, indent=2), encoding="utf-8")
