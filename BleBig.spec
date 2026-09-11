# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

lama_datas, lama_binaries, lama_hidden = collect_all("simple_lama_inpainting")
a = Analysis(["run_blebig.py"], pathex=["."], binaries=lama_binaries,
    datas=lama_datas + [("assets", "assets")], hiddenimports=lama_hidden,
    hookspath=[], runtime_hooks=[],
    excludes=["torch.utils.tensorboard", "tensorboard"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="BleBig", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=True, console=False,
    icon="assets/blebig.ico")
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name="BleBig")
