"""Post-processing effects for generated PDF documents.

Supports:
- Watermarking (custom transparent rotated text overlay)
- PDF Encryption (AES-128/256 password security)
- Handout / N-Up Page Layout (1, 2, or 4 slides per page for printing)
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import pypdf
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from slidepdf.core.models import ConversionOptions


def generate_watermark_page(
    width: float,
    height: float,
    text: str,
    opacity: float = 0.2,
    angle: float = 45.0,
    font_name: str = "Helvetica-Bold",
    color_rgb: Tuple[float, float, float] = (0.4, 0.4, 0.4),
) -> pypdf.PageObject:
    """Generate an in-memory single-page PDF containing a rotated watermark overlay."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    c.saveState()
    # Ensure opacity is clamped between 0.05 and 1.0
    safe_opacity = max(0.05, min(1.0, float(opacity)))
    r, g, b = color_rgb
    c.setFillColor(Color(r, g, b, alpha=safe_opacity))

    # Dynamically scale font size to look balanced on any slide/page dimension
    diag = (width**2 + height**2) ** 0.5
    font_size = max(18.0, min(72.0, diag / (len(text) * 0.7 + 5.0)))
    c.setFont(font_name, font_size)

    # Center and rotate text
    c.translate(width / 2.0, height / 2.0)
    c.rotate(angle)
    c.drawCentredString(0, -font_size / 3.0, text)

    c.restoreState()
    c.showPage()
    c.save()

    buf.seek(0)
    reader = pypdf.PdfReader(buf)
    return reader.pages[0]


def apply_watermark(
    input_pdf: Path,
    output_pdf: Path,
    text: str,
    opacity: float = 0.2,
) -> Path:
    """Stamp a watermark text across all pages in the PDF."""
    if not text or not text.strip():
        return input_pdf

    text = text.strip()
    reader = pypdf.PdfReader(str(input_pdf))
    writer = pypdf.PdfWriter()

    for page in reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        wm_page = generate_watermark_page(width=w, height=h, text=text, opacity=opacity)
        added_page = writer.add_page(page)
        added_page.merge_page(wm_page)

    # Copy metadata
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    # Write output (safe temp file write)
    tmp_dir = output_pdf.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=".pdf") as tmp_f:
        tmp_path = Path(tmp_f.name)
        writer.write(tmp_f)

    tmp_path.replace(output_pdf)
    return output_pdf


def apply_encryption(
    input_pdf: Path,
    output_pdf: Path,
    user_password: str,
    owner_password: Optional[str] = None,
) -> Path:
    """Encrypt the PDF with standard AES encryption password protection."""
    if not user_password:
        return input_pdf

    reader = pypdf.PdfReader(str(input_pdf))
    writer = pypdf.PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    if reader.metadata:
        writer.add_metadata(reader.metadata)

    owner_pwd = owner_password or user_password
    writer.encrypt(user_password=user_password, owner_password=owner_pwd)

    tmp_dir = output_pdf.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=".pdf") as tmp_f:
        tmp_path = Path(tmp_f.name)
        writer.write(tmp_f)

    tmp_path.replace(output_pdf)
    return output_pdf


def create_handout(
    input_pdf: Path,
    output_pdf: Path,
    slides_per_page: int = 2,
    page_size: Tuple[float, float] = A4,
) -> Path:
    """Reformat presentation slides into a multi-slide handout layout (e.g. 2-up or 4-up)."""
    if slides_per_page not in (2, 4):
        return input_pdf

    reader = pypdf.PdfReader(str(input_pdf))
    if len(reader.pages) == 0:
        return input_pdf

    page_w, page_h = page_size
    writer = pypdf.PdfWriter()

    if slides_per_page == 2:
        # 2 slides stacked vertically on portrait page
        slot_w = page_w
        slot_h = page_h / 2.0
        margin_x = 24.0
        margin_y = 20.0
        target_w = slot_w - (2 * margin_x)
        target_h = slot_h - (2 * margin_y)

        for i in range(0, len(reader.pages), 2):
            new_page = writer.add_blank_page(width=page_w, height=page_h)
            batch = reader.pages[i : i + 2]

            for slot_idx, slide_page in enumerate(batch):
                orig_w = float(slide_page.mediabox.width)
                orig_h = float(slide_page.mediabox.height)
                scale = min(target_w / orig_w, target_h / orig_h)
                scaled_w = orig_w * scale
                scaled_h = orig_h * scale

                # Slot 0 = top half, Slot 1 = bottom half
                slot_y_base = page_h / 2.0 if slot_idx == 0 else 0.0
                tx = (slot_w - scaled_w) / 2.0
                ty = slot_y_base + (slot_h - scaled_h) / 2.0

                trans = pypdf.Transformation().scale(scale, scale).translate(tx, ty)
                p_copy = pypdf.PageObject.create_blank_page(width=orig_w, height=orig_h)
                p_copy.merge_page(slide_page)
                p_copy.add_transformation(trans)
                new_page.merge_page(p_copy)

    elif slides_per_page == 4:
        # 4 slides in a 2x2 grid
        slot_w = page_w / 2.0
        slot_h = page_h / 2.0
        margin_x = 16.0
        margin_y = 16.0
        target_w = slot_w - (2 * margin_x)
        target_h = slot_h - (2 * margin_y)

        # Grid slots in reading order:
        # 0: top-left (col 0, row 1)
        # 1: top-right (col 1, row 1)
        # 2: bottom-left (col 0, row 0)
        # 3: bottom-right (col 1, row 0)
        grid_positions = [(0, 1), (1, 1), (0, 0), (1, 0)]

        for i in range(0, len(reader.pages), 4):
            new_page = writer.add_blank_page(width=page_w, height=page_h)
            batch = reader.pages[i : i + 4]

            for (col, row), slide_page in zip(grid_positions, batch):
                orig_w = float(slide_page.mediabox.width)
                orig_h = float(slide_page.mediabox.height)
                scale = min(target_w / orig_w, target_h / orig_h)
                scaled_w = orig_w * scale
                scaled_h = orig_h * scale

                slot_x_base = col * slot_w
                slot_y_base = row * slot_h
                tx = slot_x_base + (slot_w - scaled_w) / 2.0
                ty = slot_y_base + (slot_h - scaled_h) / 2.0

                trans = pypdf.Transformation().scale(scale, scale).translate(tx, ty)
                p_copy = pypdf.PageObject.create_blank_page(width=orig_w, height=orig_h)
                p_copy.merge_page(slide_page)
                p_copy.add_transformation(trans)
                new_page.merge_page(p_copy)

    tmp_dir = output_pdf.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=".pdf") as tmp_f:
        tmp_path = Path(tmp_f.name)
        writer.write(tmp_f)

    tmp_path.replace(output_pdf)
    return output_pdf


def apply_post_processing(
    pdf_path: Path,
    options: ConversionOptions,
    target_path: Optional[Path] = None,
) -> Path:
    """Apply configured post-processing effects in sequence:

    Pipeline sequence:
    1. Handout reformatting (2-up or 4-up)
    2. Watermark overlay (text + opacity)
    3. Password encryption (AES user/owner lock)
    """
    dest = target_path or pdf_path

    # Check if any post-processing is actually required
    has_handout = options.handout_mode in (2, 4)
    has_watermark = bool(options.watermark_text and options.watermark_text.strip())
    has_encryption = bool(options.password and options.password.strip())

    if not (has_handout or has_watermark or has_encryption):
        if dest != pdf_path:
            import shutil
            shutil.copy2(pdf_path, dest)
        return dest

    curr_path = pdf_path

    # Step 1: Handout layout
    if has_handout:
        curr_path = create_handout(
            input_pdf=curr_path,
            output_pdf=dest,
            slides_per_page=options.handout_mode,
        )

    # Step 2: Watermark
    if has_watermark:
        curr_path = apply_watermark(
            input_pdf=curr_path,
            output_pdf=dest,
            text=options.watermark_text,
            opacity=options.watermark_opacity,
        )

    # Step 3: Password encryption
    if has_encryption:
        curr_path = apply_encryption(
            input_pdf=curr_path,
            output_pdf=dest,
            user_password=options.password,
        )

    return dest
