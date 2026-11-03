"""Generate modern application icons for SlidePDF Studio."""

from pathlib import Path
from PIL import Image, ImageDraw


def generate_icon(output_png: Path, output_svg: Path):
    output_png.parent.mkdir(parents=True, exist_ok=True)

    # 1. Generate 256x256 PNG Icon
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background (vibrant gradient-like deep slate)
    draw.rounded_rectangle([12, 12, size - 12, size - 12], radius=48, fill=(24, 32, 47, 255))

    # PPTX Orange Page badge (left tilted/stacked)
    draw.rounded_rectangle([36, 48, 140, 208], radius=16, fill=(211, 84, 0, 240))
    # 'P' symbol
    draw.rectangle([56, 76, 72, 180], fill=(255, 255, 255, 255))
    draw.rounded_rectangle([72, 76, 120, 136], radius=12, fill=(255, 255, 255, 255))
    draw.rounded_rectangle([86, 90, 106, 122], radius=6, fill=(211, 84, 0, 255))

    # PDF Red Page badge (right stacked/overlapping)
    draw.rounded_rectangle([116, 48, 220, 208], radius=16, fill=(192, 57, 43, 240), outline=(255, 255, 255, 60), width=2)
    # Conversion Arrow Badge in the center
    draw.ellipse([98, 108, 158, 168], fill=(41, 128, 185, 255), outline=(255, 255, 255, 255), width=3)
    # Arrow icon
    draw.polygon([(118, 126), (142, 138), (118, 150)], fill=(255, 255, 255, 255))

    img.save(str(output_png), "PNG")

    # 2. Generate SVG
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="pptxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e67e22"/>
      <stop offset="100%" stop-color="#d35400"/>
    </linearGradient>
    <linearGradient id="pdfGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e74c3c"/>
      <stop offset="100%" stop-color="#c0392b"/>
    </linearGradient>
  </defs>
  <rect x="12" y="12" width="232" height="232" rx="48" fill="url(#bg)"/>
  <!-- PPTX Card -->
  <rect x="36" y="48" width="104" height="160" rx="16" fill="url(#pptxGrad)"/>
  <text x="64" y="150" font-family="sans-serif" font-weight="900" font-size="70" fill="#ffffff">P</text>
  <!-- PDF Card -->
  <rect x="116" y="48" width="104" height="160" rx="16" fill="url(#pdfGrad)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
  <!-- Arrow circle -->
  <circle cx="128" cy="138" r="30" fill="#2980b9" stroke="#ffffff" stroke-width="3"/>
  <path d="M 120 126 L 142 138 L 120 150 Z" fill="#ffffff"/>
</svg>'''
    with open(output_svg, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"Generated {output_png} and {output_svg}")


if __name__ == "__main__":
    generate_icon(Path("assets/icon.png"), Path("assets/icon.svg"))
