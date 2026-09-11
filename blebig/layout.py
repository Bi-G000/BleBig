from __future__ import annotations

from dataclasses import dataclass


PRESETS_CM = {
    "A3 dọc": (29.7, 42.0),
    "A3 ngang": (42.0, 29.7),
    "A4 dọc": (21.0, 29.7),
    "A4 ngang": (29.7, 21.0),
    "A5 dọc": (14.8, 21.0),
    "A5 ngang": (21.0, 14.8),
}


@dataclass(frozen=True)
class Layout:
    output_width_px: int
    output_height_px: int
    content_width_px: int
    content_height_px: int
    output_width_cm: float
    output_height_cm: float
    content_width_cm: float
    content_height_cm: float
    area: str


def cm_to_px(cm: float, dpi: int) -> int:
    return max(1, round(cm / 2.54 * dpi))


def calculate_layout(width_cm: float, height_cm: float, bleed_cm: float, dpi: int, placement: str, area: str = "center") -> Layout:
    if width_cm <= 0 or height_cm <= 0:
        raise ValueError("Kích thước phải lớn hơn 0 cm.")
    if bleed_cm < 0:
        raise ValueError("Khoảng tràn không được âm.")
    if placement not in {"outside", "inside"}:
        raise ValueError("Kiểu tràn không hợp lệ.")
    if area not in {"center", "left", "right", "top", "bottom"}:
        raise ValueError("Khu vực tràn không hợp lệ.")

    # Khoảng tràn là tổng phần cộng/trừ trên một chiều, đúng theo ví dụ:
    # A4 + 0.5 cm => 21.5 x 30.2; A4 trong khổ => nội dung 20.5 x 29.2.
    if placement == "outside":
        content_w_cm, content_h_cm = width_cm, height_cm
        output_w_cm = width_cm + (bleed_cm if area in {"center", "left", "right"} else 0)
        output_h_cm = height_cm + (bleed_cm if area in {"center", "top", "bottom"} else 0)
    else:
        invalid_w = area in {"center", "left", "right"} and bleed_cm >= width_cm
        invalid_h = area in {"center", "top", "bottom"} and bleed_cm >= height_cm
        if invalid_w or invalid_h:
            raise ValueError("Khoảng tràn phải nhỏ hơn kích thước thành phẩm.")
        output_w_cm, output_h_cm = width_cm, height_cm
        content_w_cm = width_cm - (bleed_cm if area in {"center", "left", "right"} else 0)
        content_h_cm = height_cm - (bleed_cm if area in {"center", "top", "bottom"} else 0)

    layout = Layout(
        cm_to_px(output_w_cm, dpi), cm_to_px(output_h_cm, dpi),
        cm_to_px(content_w_cm, dpi), cm_to_px(content_h_cm, dpi),
        output_w_cm, output_h_cm, content_w_cm, content_h_cm, area,
    )
    if layout.output_width_px * layout.output_height_px > 160_000_000:
        raise ValueError("Kích thước vượt 160 megapixel. Hãy giảm khổ hoặc DPI để tránh hết RAM.")
    return layout


def fit_size(source: tuple[int, int], bounds: tuple[int, int]) -> tuple[int, int]:
    sw, sh = source
    bw, bh = bounds
    scale = min(bw / sw, bh / sh)
    return max(1, round(sw * scale)), max(1, round(sh * scale))


def engine_anchor_for_area(area: str) -> str:
    # Khu vực chỉ phía cần sinh nền; ảnh phải neo về phía đối diện.
    return {"center":"center", "left":"right", "right":"left", "top":"bottom", "bottom":"top"}[area]
