# Image_placeholder_generator.py

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 128
RADIUS = 48
LINE_WIDTH = 2
PADDING = 8

SCRIPT_DIR = Path(__file__).parent
FONT_PATH = SCRIPT_DIR / "DejaVuSans-Bold.ttf"

MAX_FONT_SIZE = 76
MIN_FONT_SIZE = 36

for i in range(64):
    img = Image.new("RGBA", (SIZE, SIZE), (255,255,255,0))
    draw = ImageDraw.Draw(img)

    draw.ellipse(
        [(SIZE/2-RADIUS, SIZE/2-RADIUS),
         (SIZE/2+RADIUS, SIZE/2+RADIUS)],
        outline="black",
        width=LINE_WIDTH
    )

    text = str(i)

    font_size = MAX_FONT_SIZE
    while font_size >= MIN_FONT_SIZE:
        font = ImageFont.truetype(str(FONT_PATH), font_size)
        bbox = draw.textbbox((0,0), text, font=font)

        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        max_text_size = 2 * (RADIUS - PADDING)

        if text_w <= max_text_size and text_h <= max_text_size:
            break

        font_size -= 1
    
    # Recompute bbox with the chosen font
    bbox = draw.textbbox((0,0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Center the bbox inside the image, accounting for offsets
    x = (SIZE - text_w) / 2 - bbox[0]
    y = (SIZE - text_h) / 2 - bbox[1]

    draw.text((x, y), text, fill="black", font=font)

    img.save(f"{i}.png")