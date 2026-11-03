"""Script to generate rich sample PowerPoint presentations for testing."""

from __future__ import annotations

import io
from pathlib import Path
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


def create_sample_image(text: str, width: int = 400, height: int = 300, bg_color=(41, 128, 185)) -> bytes:
    """Create a sample PNG image in-memory."""
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Draw geometric graphics
    draw.rectangle([20, 20, width - 20, height - 20], outline=(255, 255, 255), width=3)
    draw.ellipse([width // 2 - 50, height // 2 - 50, width // 2 + 50, height // 2 + 50], fill=(231, 76, 60))
    # Simple lines
    draw.line([0, 0, width, height], fill=(241, 196, 15), width=2)
    draw.line([0, height, width, 0], fill=(46, 204, 113), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_presentations(output_dir: Path) -> list[Path]:
    """Generate sample test presentations."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    # 1. Basic Multi-Slide Presentation
    prs1 = Presentation()
    prs1.slide_width = Inches(13.333)  # 16:9 widescreen
    prs1.slide_height = Inches(7.5)

    # Slide 1: Title
    blank_layout = prs1.slide_layouts[6]
    s1 = prs1.slides.add_slide(blank_layout)

    # Slide 1 Title box
    tx_box = s1.shapes.add_textbox(Inches(1.5), Inches(2.0), Inches(10.33), Inches(2.0))
    tf = tx_box.text_frame
    p1 = tf.paragraphs[0]
    p1.text = "SlidePDF Studio Test Presentation"
    p1.alignment = PP_ALIGN.CENTER
    p1.font.bold = True
    p1.font.size = Pt(40)
    p1.font.color.rgb = RGBColor(41, 128, 185)

    p2 = tf.add_paragraph()
    p2.text = "High-Fidelity PPTX to PDF Conversion Suite"
    p2.alignment = PP_ALIGN.CENTER
    p2.font.italic = True
    p2.font.size = Pt(20)
    p2.font.color.rgb = RGBColor(127, 140, 141)

    # Slide 2: Bullet points and formatted text
    s2 = prs1.slides.add_slide(blank_layout)
    header_box = s2.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.33), Inches(1.0))
    hp = header_box.text_frame.paragraphs[0]
    hp.text = "Key Architecture & Features"
    hp.font.bold = True
    hp.font.size = Pt(28)
    hp.font.color.rgb = RGBColor(44, 62, 80)

    content_box = s2.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.33), Inches(4.5))
    ctf = content_box.text_frame
    bullets = [
        ("Multi-Engine Architecture", "Supports LibreOffice headless, MS Office COM, and Native Python engines.", 0),
        ("Universal Compatibility", "Runs on Linux, Windows, and macOS without strict external dependencies.", 1),
        ("Batch & Merge Modes", "Converts thousands of slides and merges them into indexed consolidated PDFs.", 0),
        ("High-DPI Desktop Interface", "Built with modern CustomTkinter, dark mode, and multi-threaded workers.", 1),
    ]

    for title, desc, level in bullets:
        bp = ctf.add_paragraph()
        bp.level = level
        run_title = bp.add_run()
        run_title.text = f"{title}: "
        run_title.font.bold = True
        run_title.font.size = Pt(16)
        run_title.font.color.rgb = RGBColor(52, 73, 94)

        run_desc = bp.add_run()
        run_desc.text = desc
        run_desc.font.size = Pt(16)
        run_desc.font.color.rgb = RGBColor(80, 80, 80)

    # Slide 3: Tables and Data
    s3 = prs1.slides.add_slide(blank_layout)
    th_box = s3.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.33), Inches(1.0))
    thp = th_box.text_frame.paragraphs[0]
    thp.text = "Engine Capability Matrix"
    thp.font.bold = True
    thp.font.size = Pt(28)
    thp.font.color.rgb = RGBColor(44, 62, 80)

    # Add Table: 4 rows, 4 columns
    table_shape = s3.shapes.add_table(4, 4, Inches(1.0), Inches(2.2), Inches(11.33), Inches(3.0))
    table = table_shape.table

    headers = ["Engine Name", "Platform", "External Requirements", "Render Fidelity"]
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = header
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(41, 128, 185)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ["LibreOffice Engine", "Linux, macOS, Windows", "LibreOffice / soffice", "High (Vector)"],
        ["MS Office COM Engine", "Windows Only", "Microsoft PowerPoint", "Pixel-Perfect Native"],
        ["Native Python Engine", "Cross-Platform (Universal)", "None (Pure Python)", "Standard Vector"],
    ]

    for row_idx, row_data in enumerate(data, start=1):
        for col_idx, text in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            cell.text = text
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.color.rgb = RGBColor(40, 40, 40)

    # Slide 4: Embedded Images & Graphics
    s4 = prs1.slides.add_slide(blank_layout)
    ih_box = s4.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.33), Inches(1.0))
    ihp = ih_box.text_frame.paragraphs[0]
    ihp.text = "Embedded Visuals and Diagrams"
    ihp.font.bold = True
    ihp.font.size = Pt(28)
    ihp.font.color.rgb = RGBColor(44, 62, 80)

    # Embed sample image
    img_data = create_sample_image("Demo Chart", width=600, height=400, bg_color=(39, 174, 96))
    img_stream = io.BytesIO(img_data)
    s4.shapes.add_picture(img_stream, Inches(1.0), Inches(2.0), width=Inches(5.0), height=Inches(3.5))

    # Add descriptive text next to image
    img_desc_box = s4.shapes.add_textbox(Inches(6.5), Inches(2.2), Inches(5.8), Inches(3.0))
    itf = img_desc_box.text_frame
    ip = itf.paragraphs[0]
    ip.text = "Dynamic Visual Elements"
    ip.font.bold = True
    ip.font.size = Pt(18)
    ip.font.color.rgb = RGBColor(39, 174, 96)

    ip2 = itf.add_paragraph()
    ip2.text = (
        "This slide contains embedded raster graphics, tested for compression, "
        "DPI preservation, and clean vector PDF bounding boxes."
    )
    ip2.font.size = Pt(14)
    ip2.font.color.rgb = RGBColor(60, 60, 60)

    p1_path = output_dir / "sample_presentation.pptx"
    prs1.save(str(p1_path))
    created_files.append(p1_path)

    # 2. Second Presentation for Batch & Merge testing
    prs2 = Presentation()
    prs2.slide_width = Inches(13.333)
    prs2.slide_height = Inches(7.5)

    s2_1 = prs2.slides.add_slide(blank_layout)
    s2_box = s2_1.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.33), Inches(2.0))
    p_s2 = s2_box.text_frame.paragraphs[0]
    p_s2.text = "Second Presentation for Batch Merge"
    p_s2.font.bold = True
    p_s2.font.size = Pt(36)
    p_s2.font.color.rgb = RGBColor(142, 68, 173)

    p2_path = output_dir / "sample_appendix.pptx"
    prs2.save(str(p2_path))
    created_files.append(p2_path)

    print(f"Generated {len(created_files)} presentations in {output_dir}")
    return created_files


if __name__ == "__main__":
    import sys
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("samples")
    generate_presentations(out_dir)
