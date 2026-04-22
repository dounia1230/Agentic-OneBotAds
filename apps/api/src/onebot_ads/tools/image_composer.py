import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_width, target_height = size
    src_width, src_height = image.size
    scale = max(target_width / src_width, target_height / src_height)
    resized = image.resize((int(src_width * scale), int(src_height * scale)))
    left = max((resized.width - target_width) // 2, 0)
    top = max((resized.height - target_height) // 2, 0)
    return resized.crop((left, top, left + target_width, top + target_height))


def compose_publication_image(
    background_path: str,
    headline: str,
    cta: str,
    product_name: str | None = None,
    output_dir: str = "outputs/images",
) -> dict:
    try:
        background = Image.open(background_path).convert("RGBA")
        canvas = _fit_cover(background, (1080, 1080))
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        panel_bounds = (64, 640, 1016, 1016)
        draw.rounded_rectangle(panel_bounds, radius=32, fill=(14, 22, 32, 178))

        product_font = _load_font(34, bold=True)
        headline_font = _load_font(62, bold=True)
        cta_font = _load_font(32, bold=True)

        x_start = 112
        y_cursor = 700
        if product_name:
            draw.text(
                (x_start, y_cursor),
                product_name,
                font=product_font,
                fill=(209, 225, 255, 255),
            )
            y_cursor += 70

        wrapped_headline = textwrap.fill(headline, width=26)
        draw.multiline_text(
            (x_start, y_cursor),
            wrapped_headline,
            font=headline_font,
            fill=(255, 255, 255, 255),
            spacing=12,
        )
        headline_bbox = draw.multiline_textbbox(
            (x_start, y_cursor),
            wrapped_headline,
            font=headline_font,
            spacing=12,
        )
        y_cursor = headline_bbox[3] + 44

        cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
        button_width = (cta_bbox[2] - cta_bbox[0]) + 52
        button_height = (cta_bbox[3] - cta_bbox[1]) + 34
        button_bounds = (x_start, y_cursor, x_start + button_width, y_cursor + button_height)
        draw.rounded_rectangle(button_bounds, radius=22, fill=(76, 164, 255, 255))
        draw.text((x_start + 26, y_cursor + 15), cta, font=cta_font, fill=(10, 23, 40, 255))

        composed = Image.alpha_composite(canvas, overlay).convert("RGB")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = output_path / f"publication_{int(time.time())}.png"
        composed.save(filename)
        return {"status": "composed", "image_path": str(filename)}
    except Exception as exc:
        return {
            "status": "composition_failed",
            "image_path": None,
            "error": str(exc),
        }
