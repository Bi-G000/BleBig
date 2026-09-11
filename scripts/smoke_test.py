import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw
from blebig.engine import ExpandOptions, expand_fast
from blebig.layout import calculate_layout, engine_anchor_for_area

image = Image.new("RGB", (320, 200), "#d8b37a")
draw = ImageDraw.Draw(image)
draw.ellipse((110, 50, 210, 150), fill="#3f6b41")
result = expand_fast(image, ExpandOptions(500, 400))
assert result.size == (500, 400)
assert result.crop((90, 100, 410, 300)).tobytes() == image.tobytes()
print("BleBig smoke test: PASS")

outside = calculate_layout(21, 29.7, .5, 300, "outside")
inside = calculate_layout(21, 29.7, .5, 300, "inside")
assert (outside.output_width_cm, outside.output_height_cm) == (21.5, 30.2)
assert inside.content_width_px == round(20.5 / 2.54 * 300)
assert inside.content_height_px == round(29.2 / 2.54 * 300)
print("BleBig layout test: PASS")

left = calculate_layout(29.7, 21, .3, 300, "inside", "left")
assert left.output_width_cm == 29.7 and left.output_height_cm == 21
assert left.content_width_cm == 29.4 and left.content_height_cm == 21
assert engine_anchor_for_area("left") == "right"
print("BleBig directional bleed test: PASS")
