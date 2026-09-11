from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Tạo gói cập nhật tăng dần cho BleBig")
    parser.add_argument("--version", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--change", action="append", default=[])
    parser.add_argument("--all", action="store_true", help="Đóng gói toàn bộ thư mục root")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    if args.all:
        ignored = {"BleBigUpdater.exe"}
        files = [p.relative_to(args.root) for p in args.root.rglob("*")
            if p.is_file() and p.name not in ignored and "Update" not in p.relative_to(args.root).parts]
    else:
        files = [Path(value) for value in args.files]
    if not files: raise SystemExit("Không có file để đóng gói")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(files):
            value = str(relative)
            if relative.is_absolute() or ".." in relative.parts: raise SystemExit(f"Đường dẫn không hợp lệ: {value}")
            raw = (args.root / relative).read_bytes()
            entries.append({"path": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest()})
            archive.writestr("payload/" + relative.as_posix(), raw)
        manifest = {"app_id":"com.thienha.blebig", "version":args.version,
            "changes":args.change or ["Cải thiện độ ổn định"], "files":entries}
        archive.writestr("blebig-update.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    print(args.output)


if __name__ == "__main__": main()
