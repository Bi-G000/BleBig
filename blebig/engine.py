from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from .paths import model_dir
from .layout import fit_size


LOG = logging.getLogger("blebig.engine")


@dataclass(frozen=True)
class ExpandOptions:
    width: int
    height: int
    anchor: str = "center"
    mode: str = "fast"
    feather: int = 24


def _placement(src_w: int, src_h: int, dst_w: int, dst_h: int, anchor: str) -> tuple[int, int]:
    x = (dst_w - src_w) // 2
    y = (dst_h - src_h) // 2
    if anchor == "left":
        x = 0
    elif anchor == "right":
        x = dst_w - src_w
    elif anchor == "top":
        y = 0
    elif anchor == "bottom":
        y = dst_h - src_h
    return max(0, x), max(0, y)


def _prepare(image: Image.Image, options: ExpandOptions):
    src = image.convert("RGB")
    sw, sh = src.size
    if options.width < sw or options.height < sh:
        raise ValueError("Khung mới phải lớn hơn hoặc bằng ảnh gốc. BleBig không crop ảnh.")
    x, y = _placement(sw, sh, options.width, options.height, options.anchor)
    arr = np.asarray(src)
    top, bottom = y, options.height - sh - y
    left, right = x, options.width - sw - x
    seeded = cv2.copyMakeBorder(arr, top, bottom, left, right, cv2.BORDER_REFLECT_101)
    original_mask = np.zeros((options.height, options.width), np.uint8)
    original_mask[y : y + sh, x : x + sw] = 255
    return src, seeded, original_mask, x, y


def fit_for_content(image: Image.Image, width: int, height: int) -> Image.Image:
    size = fit_size(image.size, (width, height))
    if size == image.size:
        return image.convert("RGB")
    return image.convert("RGB").resize(size, Image.Resampling.LANCZOS)


def _composite_original(result: Image.Image, original: Image.Image, x: int, y: int) -> Image.Image:
    # Pixel của ảnh nguồn luôn được trả lại sau cùng; AI chỉ được phép sửa phần tràn.
    result = result.convert("RGB")
    result.paste(original, (x, y))
    return result


def expand_fast(image: Image.Image, options: ExpandOptions) -> Image.Image:
    original, seeded, keep, x, y = _prepare(image, options)
    # Làm mượt phần nền phản chiếu nhưng không đụng vùng ảnh gốc.
    sigma = max(1.0, options.feather / 3)
    smooth = cv2.GaussianBlur(seeded, (0, 0), sigmaX=sigma, sigmaY=sigma)
    distance = cv2.distanceTransform(255 - keep, cv2.DIST_L2, 5)
    alpha = np.clip(distance / max(1, options.feather), 0, 1)[..., None]
    mixed = (seeded * (1 - alpha) + smooth * alpha).astype(np.uint8)
    return _composite_original(Image.fromarray(mixed), original, x, y)


def expand_ai(image: Image.Image, options: ExpandOptions, progress=None) -> Image.Image:
    original, seeded, keep, x, y = _prepare(image, options)
    if progress:
        progress("Đang nạp AI LaMa; lần đầu có thể cần tải model…")
    os.environ.setdefault("TORCH_HOME", str(model_dir()))
    # PyInstaller GUI không tạo stdout/stderr. simple-lama ghi tiến độ tải model
    # vào stderr nên cần một stream thật để tránh AttributeError.
    if sys.stderr is None:
        sys.stderr = open(model_dir() / "model-download.log", "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = open(model_dir() / "model-download.log", "a", encoding="utf-8", buffering=1)
    try:
        import truststore
        truststore.inject_into_ssl()
    except Exception:
        LOG.warning("Không kích hoạt được Windows Certificate Store", exc_info=True)
    from simple_lama_inpainting import SimpleLama

    # Hạn chế VRAM/RAM. Kết quả được phóng về khổ đích và ghép lại ảnh gốc.
    max_side = 2048
    scale = min(1.0, max_side / max(options.width, options.height))
    work = Image.fromarray(seeded)
    mask = Image.fromarray(255 - keep).convert("L")
    if scale < 1:
        size = (max(64, round(options.width * scale)), max(64, round(options.height * scale)))
        work = work.resize(size, Image.Resampling.LANCZOS)
        mask = mask.resize(size, Image.Resampling.NEAREST)
    lama = SimpleLama()
    generated = lama(work, mask)
    if generated.size != (options.width, options.height):
        generated = generated.resize((options.width, options.height), Image.Resampling.LANCZOS)
    return _composite_original(generated, original, x, y)


def expand(image: Image.Image, options: ExpandOptions, progress=None) -> Image.Image:
    LOG.info("Bắt đầu: source=%s target=%sx%s mode=%s anchor=%s", image.size, options.width, options.height, options.mode, options.anchor)
    if image.size == (options.width, options.height):
        LOG.info("Không có vùng cần tràn; trả lại ảnh gốc")
        return image.convert("RGB").copy()
    if options.mode == "ai":
        result = expand_ai(image, options, progress)
    else:
        result = expand_fast(image, options)
    LOG.info("Hoàn tất: output=%s", result.size)
    return result
