# -*- mode: python ; coding: utf-8 -*-
a = Analysis(["run_updater.py"], pathex=["."], binaries=[], datas=[],
    hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=["PySide6", "PIL", "numpy", "cv2", "torch"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="BleBigUpdater",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True,
    console=False, icon="assets/blebig.ico")
