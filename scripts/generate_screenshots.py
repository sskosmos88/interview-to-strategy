"""Generate README screenshots using Pillow.

Renders a fake terminal window and a markdown preview window.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_font(preferred: list[str], fallback_size: int) -> ImageFont.FreeTypeFont:
    candidates = []
    for name in preferred:
        candidates.append(Path(r"C:\Windows\Fonts") / name)
        candidates.append(Path.home() / ".fonts" / name)
        candidates.append(Path("/usr/share/fonts/truetype") / name)
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), fallback_size)
    return ImageFont.load_default()


def hex_color(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill: tuple, outline: tuple | None = None, width: int = 1) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def make_terminal_screenshot(output_path: str) -> None:
    width, height = 900, 520
    bg = hex_color("#1e1e1e")
    title_bar = hex_color("#2d2d2d")
    text_color = hex_color("#cccccc")
    green = hex_color("#4ec9b0")
    yellow = hex_color("#f9f1a5")
    blue = hex_color("#569cd6")
    magenta = hex_color("#c586c0")
    red = hex_color("#f48771")

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([0, 0, width, 32], fill=title_bar)
    font_title = find_font(["segoeui.ttf", "arial.ttf"], 13)
    draw.text((40, 8), "Windows PowerShell", fill=text_color, font=font_title)

    # Window controls (fake)
    for i, color in enumerate([red, yellow, green]):
        cx = width - 60 + i * 22
        draw.ellipse([cx, 10, cx + 12, 22], fill=color)

    # Content
    font = find_font(["consola.ttf", "cour.ttf", "segoeui.ttf", "arial.ttf"], 15)
    line_height = 24
    x, y = 20, 52

    prompt = r"PS C:\Users\Thunderobot\eltor\diploma-zerocoder>"
    cmd = " python main.py --input data/sample-transcript.txt --name \"Иван Петров\" --output output/strategy.md --producer-name \"Алёна Орлова\" --producer-telegram \"@alena_prod\""

    draw.text((x, y), prompt, fill=blue, font=font)
    px = x + font.getlength(prompt)
    draw.text((px + 4, y), cmd, fill=text_color, font=font)
    y += line_height * 2

    outputs = [
        ("[INFO] Analyzing transcript (2241 chars)...", text_color),
        ("[INFO] Provider: ollama", text_color),
        ("[INFO] Rendering strategy document for 'Иван Петров'...", text_color),
        ("[DONE] Strategy written to: output\\strategy.md", green),
        ("", text_color),
        ("PS C:\\Users\\Thunderobot\\eltor\\diploma-zerocoder>", blue),
    ]
    for line, color in outputs:
        draw.text((x, y), line, fill=color, font=font)
        y += line_height

    # Subtle shadow/reflection
    draw.rectangle([0, height - 4, width, height], fill=title_bar)

    img.save(output_path, "PNG")
    print(f"Saved terminal screenshot: {output_path}")


def make_output_preview_screenshot(md_path: str, output_path: str) -> None:
    width = 820
    bg = hex_color("#ffffff")
    header_bg = hex_color("#f6f8fa")
    border = hex_color("#d0d7de")
    text_color = hex_color("#24292f")
    heading_color = hex_color("#0969da")
    muted = hex_color("#656d76")
    quote_bg = hex_color("#f6f8fa")
    table_header = hex_color("#f6f8fa")
    table_border = hex_color("#d0d7de")

    img = Image.new("RGB", (width, 1200), bg)
    draw = ImageDraw.Draw(img)

    # Window chrome
    draw.rectangle([0, 0, width, 36], fill=header_bg)
    draw.line([(0, 36), (width, 36)], fill=border, width=1)
    for i, color in enumerate([hex_color("#ff5f56"), hex_color("#ffbd2e"), hex_color("#27c93f")]):
        draw.ellipse([14 + i * 18, 12, 26 + i * 18, 24], fill=color)
    font_title = find_font(["segoeui.ttf", "arial.ttf"], 13)
    draw.text((70, 10), "output/strategy.md - Preview", fill=text_color, font=font_title)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Use a fixed-height canvas and crop later based on content
    font_h1 = find_font(["segoeui.ttf", "arial.ttf"], 22)
    font_h2 = find_font(["segoeui.ttf", "arial.ttf"], 18)
    font_h3 = find_font(["segoeui.ttf", "arial.ttf"], 15)
    font_body = find_font(["segoeui.ttf", "arial.ttf"], 14)
    font_small = find_font(["segoeui.ttf", "arial.ttf"], 12)

    margin_x = 30
    max_w = width - margin_x * 2
    y = 60

    def draw_wrapped(text: str, font: ImageFont.FreeTypeFont, color: tuple, indent: int = 0) -> None:
        nonlocal y
        lines = wrap_text(text, font, max_w - indent)
        for line in lines:
            draw.text((margin_x + indent, y), line, fill=color, font=font)
            y += font.size + 6

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            y += 8
            i += 1
            continue

        if stripped.startswith("# "):
            y += 10
            draw_wrapped(stripped[2:], font_h1, heading_color)
            draw.line([(margin_x, y - 4), (width - margin_x, y - 4)], fill=border, width=1)
            y += 10
        elif stripped.startswith("## "):
            y += 8
            draw_wrapped(stripped[3:], font_h2, heading_color)
            y += 4
        elif stripped.startswith("### "):
            y += 6
            draw_wrapped(stripped[4:], font_h3, text_color)
            y += 2
        elif stripped.startswith("**") and stripped.endswith("**"):
            # bold paragraph
            draw_wrapped(stripped.strip("*"), font_body, text_color)
        elif stripped.startswith("> "):
            quote_text = stripped[2:]
            q_lines = wrap_text(quote_text, font_body, max_w - 24)
            qh = len(q_lines) * (font_body.size + 6) + 12
            draw.rectangle([margin_x, y, width - margin_x, y + qh], fill=quote_bg)
            draw.line([(margin_x, y), (margin_x, y + qh)], fill=heading_color, width=3)
            for ql in q_lines:
                draw.text((margin_x + 12, y + 6), ql, fill=text_color, font=font_body)
                y += font_body.size + 6
            y += 12
        elif stripped.startswith("- "):
            bullet = "• " + stripped[2:]
            draw_wrapped(bullet, font_body, text_color, indent=0)
        elif stripped.startswith("1. ") or stripped.startswith("2. ") or stripped.startswith("3. "):
            draw_wrapped(stripped, font_body, text_color, indent=0)
        elif "|" in stripped and "---" not in stripped:
            # Table row - render a simple row
            cells = [c.strip() for c in stripped.split("|")]
            cells = [c for c in cells if c]
            if cells:
                col_w = (max_w - 20) // max(len(cells), 1)
                row_h = font_small.size + 14
                x = margin_x
                for idx, cell in enumerate(cells):
                    fill = table_header if i == 0 or (i > 0 and lines[i - 1].strip().startswith("|")) and "---" in lines[i - 1].strip() else bg
                    draw.rectangle([x, y, x + col_w, y + row_h], fill=fill, outline=table_border)
                    cell_lines = wrap_text(cell, font_small, col_w - 10)
                    cy = y + 6
                    for cl in cell_lines[:2]:
                        draw.text((x + 6, cy), cl, fill=text_color, font=font_small)
                        cy += font_small.size + 2
                    x += col_w
                y += row_h
        else:
            draw_wrapped(stripped, font_body, text_color)

        i += 1

    # Crop to content with padding
    crop_y = min(y + 40, 1180)
    img = img.crop((0, 0, width, crop_y))
    img.save(output_path, "PNG")
    print(f"Saved output preview screenshot: {output_path}")


def main() -> int:
    repo_root = Path(__file__).parent.parent
    screenshots_dir = repo_root / "docs" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    terminal_path = screenshots_dir / "terminal-run.png"
    output_path = screenshots_dir / "output-preview.png"
    md_path = repo_root / "output" / "strategy-ollama.md"

    make_terminal_screenshot(str(terminal_path))
    make_output_preview_screenshot(str(md_path), str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
