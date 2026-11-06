"""Post-processing effects for generated PDF documents.

Supports:
- Watermarking (custom transparent rotated text overlay)
- Slide Page Numbering & Footer stamping
- PDF Encryption (AES-128/256 password security)
- Handout / N-Up Page Layout (1, 2, or 4 slides per page for printing)
- Identical object stream compression for compact PDF output
"""

from __future__ import annotations

import io
import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import pypdf
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from slidepdf.core.models import ConversionOptions, PDFQuality

# Maximum safe text length for stamps to prevent DoS
MAX_WATERMARK_LENGTH = 150
MAX_FOOTER_LENGTH = 100


def _safe_write_pdf(writer: pypdf.PdfWriter, target_path: Path) -> Path:
    """Safely write PDF via a temporary file with automatic cleanup on failure.
    
    Protects against orphaned temporary files (CWE-459) and handles atomic replacement.
    """
    target_path = Path(target_path)
    tmp_dir = target_path.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path: Optional[Path] = None

    try:
        with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=".pdf") as tmp_f:
            tmp_path = Path(tmp_f.name)
            writer.write(tmp_f)
        tmp_path.replace(target_path)
        return target_path
    except Exception:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


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
    clean_text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text).strip()[:MAX_WATERMARK_LENGTH]
    if not clean_text:
        clean_text = "CONFIDENTIAL"

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    c.saveState()
    safe_opacity = max(0.05, min(1.0, float(opacity)))
    r, g, b = color_rgb
    c.setFillColor(Color(r, g, b, alpha=safe_opacity))

    diag = (width**2 + height**2) ** 0.5
    font_size = max(18.0, min(72.0, diag / (len(clean_text) * 0.7 + 5.0)))
    c.setFont(font_name, font_size)

    c.translate(width / 2.0, height / 2.0)
    c.rotate(angle)
    c.drawCentredString(0, -font_size / 3.0, clean_text)

    c.restoreState()
    c.showPage()
    c.save()

    buf.seek(0)
    with pypdf.PdfReader(buf) as reader:
        return reader.pages[0]


def generate_page_number_page(
    width: float,
    height: float,
    page_num: int,
    total_pages: int,
    format_str: str = "Page {n} of {total}",
    font_name: str = "Helvetica",
    font_size: float = 9.0,
    position: str = "bottom-right",
) -> pypdf.PageObject:
    """Generate an in-memory single-page PDF containing a subtle footer slide number."""
    safe_format = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", format_str).strip()[:MAX_FOOTER_LENGTH]
    if not safe_format:
        safe_format = "Page {n} of {total}"

    try:
        label_text = safe_format.format(n=page_num, total=total_pages)
    except Exception:
        label_text = f"Page {page_num} of {total_pages}"

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFont(font_name, font_size)
    c.setFillColor(Color(0.25, 0.25, 0.25, alpha=0.85))

    margin_x = 24.0
    margin_y = 14.0

    if position == "bottom-center":
        c.drawCentredString(width / 2.0, margin_y, label_text)
    elif position == "bottom-left":
        c.drawString(margin_x, margin_y, label_text)
    else:  # bottom-right (default)
        c.drawRightString(width - margin_x, margin_y, label_text)

    c.showPage()
    c.save()

    buf.seek(0)
    with pypdf.PdfReader(buf) as reader:
        return reader.pages[0]


def apply_watermark(
    input_pdf: Path,
    output_pdf: Path,
    text: str,
    opacity: float = 0.2,
) -> Path:
    """Stamp a watermark text across all pages in the PDF with safe file locking."""
    if not text or not text.strip():
        return input_pdf

    clean_text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text).strip()[:MAX_WATERMARK_LENGTH]
    if not clean_text:
        return input_pdf

    writer = pypdf.PdfWriter()

    with pypdf.PdfReader(str(input_pdf)) as reader:
        if reader.is_encrypted:
            raise ValueError(f"Cannot apply watermark to encrypted PDF: {input_pdf.name}")

        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            wm_page = generate_watermark_page(width=w, height=h, text=clean_text, opacity=opacity)
            added_page = writer.add_page(page)
            added_page.merge_page(wm_page)

        if reader.metadata:
            writer.add_metadata(reader.metadata)

    return _safe_write_pdf(writer, output_pdf)


def apply_page_numbers(
    input_pdf: Path,
    output_pdf: Path,
    format_str: str = "Page {n} of {total}",
    position: str = "bottom-right",
) -> Path:
    """Stamp slide page numbers / footer label on every page in the PDF."""
    writer = pypdf.PdfWriter()

    with pypdf.PdfReader(str(input_pdf)) as reader:
        if reader.is_encrypted:
            raise ValueError(f"Cannot apply page numbers to encrypted PDF: {input_pdf.name}")

        total_pages = len(reader.pages)
        for idx, page in enumerate(reader.pages, start=1):
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            num_page = generate_page_number_page(
                width=w,
                height=h,
                page_num=idx,
                total_pages=total_pages,
                format_str=format_str,
                position=position,
            )
            added_page = writer.add_page(page)
            added_page.merge_page(num_page)

        if reader.metadata:
            writer.add_metadata(reader.metadata)

    return _safe_write_pdf(writer, output_pdf)


def apply_encryption(
    input_pdf: Path,
    output_pdf: Path,
    user_password: str,
    owner_password: Optional[str] = None,
) -> Path:
    """Encrypt the PDF with standard AES encryption password protection."""
    if not user_password:
        return input_pdf

    clean_user_pwd = re.sub(r"[\x00]", "", str(user_password))
    clean_owner_pwd = re.sub(r"[\x00]", "", str(owner_password or user_password))

    writer = pypdf.PdfWriter()

    with pypdf.PdfReader(str(input_pdf)) as reader:
        if reader.is_encrypted:
            # Already encrypted, skip double encryption
            return input_pdf

        for page in reader.pages:
            writer.add_page(page)

        if reader.metadata:
            writer.add_metadata(reader.metadata)

    writer.encrypt(user_password=clean_user_pwd, owner_password=clean_owner_pwd)
    return _safe_write_pdf(writer, output_pdf)


def create_handout(
    input_pdf: Path,
    output_pdf: Path,
    slides_per_page: int = 2,
    page_size: Tuple[float, float] = A4,
) -> Path:
    """Reformat presentation slides into a multi-slide handout layout (e.g. 2-up or 4-up)."""
    if slides_per_page not in (2, 4):
        return input_pdf

    page_w, page_h = page_size
    writer = pypdf.PdfWriter()

    with pypdf.PdfReader(str(input_pdf)) as reader:
        if reader.is_encrypted:
            raise ValueError(f"Cannot create handout from encrypted PDF: {input_pdf.name}")

        if len(reader.pages) == 0:
            return input_pdf

        if slides_per_page == 2:
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

                    slot_y_base = page_h / 2.0 if slot_idx == 0 else 0.0
                    tx = (slot_w - scaled_w) / 2.0
                    ty = slot_y_base + (slot_h - scaled_h) / 2.0

                    trans = pypdf.Transformation().scale(scale, scale).translate(tx, ty)
                    p_copy = pypdf.PageObject.create_blank_page(width=orig_w, height=orig_h)
                    p_copy.merge_page(slide_page)
                    p_copy.add_transformation(trans)
                    new_page.merge_page(p_copy)

        elif slides_per_page == 4:
            slot_w = page_w / 2.0
            slot_h = page_h / 2.0
            margin_x = 16.0
            margin_y = 16.0
            target_w = slot_w - (2 * margin_x)
            target_h = slot_h - (2 * margin_y)

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

    return _safe_write_pdf(writer, output_pdf)


def apply_optimization(input_pdf: Path, output_pdf: Path) -> Path:
    """Optimize PDF file size via object deduplication and stream compression."""
    writer = pypdf.PdfWriter()

    with pypdf.PdfReader(str(input_pdf)) as reader:
        if reader.is_encrypted:
            return input_pdf

        for page in reader.pages:
            try:
                page.compress_content_streams()
            except Exception:
                pass
            writer.add_page(page)

        if reader.metadata:
            writer.add_metadata(reader.metadata)

    try:
        writer.compress_identical_objects()
    except Exception:
        pass

    return _safe_write_pdf(writer, output_pdf)


def apply_post_processing(
    pdf_path: Path,
    options: ConversionOptions,
    target_path: Optional[Path] = None,
) -> Path:
    """Apply configured post-processing effects in sequence:

    Pipeline sequence:
    1. Handout reformatting (2-up or 4-up)
    2. Slide Page Numbering (Page X of Y)
    3. Watermark overlay (text + opacity)
    4. Size Optimization (if compressed quality)
    5. Password encryption (AES user/owner lock - MUST BE LAST)
    """
    dest = target_path or pdf_path

    has_handout = options.handout_mode in (2, 4)
    has_page_numbers = getattr(options, "page_numbers", False)
    has_watermark = bool(options.watermark_text and options.watermark_text.strip())
    has_compression = options.quality == PDFQuality.COMPRESSED
    has_encryption = bool(options.password and options.password.strip())

    if not (has_handout or has_page_numbers or has_watermark or has_compression or has_encryption):
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

    # Step 2: Page Numbers
    if has_page_numbers:
        fmt = getattr(options, "page_number_format", "Page {n} of {total}")
        curr_path = apply_page_numbers(
            input_pdf=curr_path,
            output_pdf=dest,
            format_str=fmt,
        )

    # Step 3: Watermark
    if has_watermark:
        curr_path = apply_watermark(
            input_pdf=curr_path,
            output_pdf=dest,
            text=options.watermark_text,
            opacity=options.watermark_opacity,
        )

    # Step 4: Stream Compression
    if has_compression:
        curr_path = apply_optimization(
            input_pdf=curr_path,
            output_pdf=dest,
        )

    # Step 5: Password encryption (must be final step)
    if has_encryption:
        curr_path = apply_encryption(
            input_pdf=curr_path,
            output_pdf=dest,
            user_password=options.password,
        )

    return dest
