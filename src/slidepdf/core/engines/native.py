"""Pure Python conversion engine using python-pptx, Pillow, and ReportLab.

Renders presentation slides directly to a PDF canvas without requiring
external office suites (such as LibreOffice or Microsoft Office).
"""

from __future__ import annotations

import io
import math
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from slidepdf.core.engines.base import BaseEngine
from slidepdf.core.models import ConversionJob, ConversionOptions, EngineType, PDFQuality
from slidepdf.core.utils import get_default_output_path, parse_slide_range


class NativePythonEngine(BaseEngine):
    """Native Python renderer based on python-pptx and ReportLab."""

    @property
    def name(self) -> str:
        return "Native Python Engine"

    @property
    def engine_type(self) -> EngineType:
        return EngineType.NATIVE

    def is_available(self) -> bool:
        """Native engine is always available as dependencies are bundled."""
        return True

    def get_details(self) -> str:
        import pptx
        import reportlab
        return f"Bundled pure-Python renderer (python-pptx {pptx.__version__}, ReportLab {reportlab.__version__})"

    def convert(
        self,
        job: ConversionJob,
        options: ConversionOptions,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        input_path = job.input_path
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Determine target output path
        output_path = job.output_path or get_default_output_path(
            input_path,
            output_dir=options.output_dir,
            prefix=options.prefix,
            suffix=options.suffix,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ext = input_path.suffix.lower()

        # Handle raster images directly to PDF page
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
            return self._convert_image(job, output_path, options, progress_callback)

        if progress_callback:
            progress_callback(0.05, f"Parsing presentation structure ({ext})...")

        try:
            prs = Presentation(str(input_path))
        except Exception as exc:
            if ext in (".ppt", ".odp"):
                raise RuntimeError(
                    f"Format '{ext}' requires LibreOffice on this system to render. "
                    f"Please install LibreOffice (e.g. 'sudo pacman -S libreoffice-fresh') or convert to .pptx."
                ) from exc
            raise RuntimeError(f"Failed to read presentation {input_path.name}: {exc}") from exc

        total_slides = len(prs.slides)
        job.total_slides = total_slides

        if total_slides == 0:
            raise ValueError(f"The presentation contains no slides: {input_path}")

        # Parse slide ranges
        target_indices = parse_slide_range(options.slide_range, total_slides)
        job.slides_to_convert = target_indices

        if not target_indices:
            raise ValueError("No matching slides found for the specified range.")

        # Slide dimensions in points (72 points = 1 inch)
        slide_w_pt = float(prs.slide_width.pt)
        slide_h_pt = float(prs.slide_height.pt)

        c = canvas.Canvas(str(output_path), pagesize=(slide_w_pt, slide_h_pt))
        c.setTitle(input_path.stem)
        c.setCreator("SlidePDF Studio (Native Engine)")

        num_targets = len(target_indices)

        for step_idx, slide_num in enumerate(target_indices, start=1):
            if progress_callback:
                pct = 0.1 + (0.85 * (step_idx / num_targets))
                progress_callback(pct, f"Rendering slide {slide_num} of {total_slides}...")

            slide = prs.slides[slide_num - 1]
            self._render_slide(c, slide, slide_w_pt, slide_h_pt, options)
            c.showPage()

        c.save()

        if progress_callback:
            progress_callback(1.0, "Conversion completed successfully.")

        job.output_path = output_path
        return output_path

    def _convert_image(
        self,
        job: ConversionJob,
        output_path: Path,
        options: ConversionOptions,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        """Convert a standalone image directly into a clean vector PDF page."""
        input_path = job.input_path
        job.total_slides = 1
        job.slides_to_convert = [1]

        if progress_callback:
            progress_callback(0.2, f"Opening image {input_path.name}...")

        try:
            pil_img = Image.open(input_path)
            # Verify file integrity
            pil_img.verify()
            pil_img = Image.open(input_path)
        except Image.DecompressionBombError as dbe:
            raise ValueError(f"Image {input_path.name} exceeds maximum safe dimensions: {dbe}") from dbe
        except Exception as exc:
            raise ValueError(f"Corrupted or invalid image file {input_path.name}: {exc}") from exc

        img_w, img_h = pil_img.size

        # 1 px = 0.75 points (at 96 DPI screen standard)
        w_pt = img_w * 0.75
        h_pt = img_h * 0.75

        c = canvas.Canvas(str(output_path), pagesize=(w_pt, h_pt))
        c.setTitle(input_path.stem)
        c.setCreator("SlidePDF Studio")

        if progress_callback:
            progress_callback(0.6, "Rendering image onto PDF canvas...")

        if options.quality == PDFQuality.COMPRESSED and (img_w > 1600 or img_h > 1600):
            pil_img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            if pil_img.mode in ("RGBA", "P"):
                pil_img.save(buf, format="PNG", optimize=True)
            else:
                pil_img.convert("RGB").save(buf, format="JPEG", quality=75, optimize=True)
            buf.seek(0)
            img_reader = ImageReader(buf)
        else:
            img_reader = ImageReader(input_path)

        c.drawImage(img_reader, 0, 0, width=w_pt, height=h_pt, mask="auto")
        c.showPage()
        c.save()

        if progress_callback:
            progress_callback(1.0, "Conversion completed.")

        job.output_path = output_path
        return output_path

    def _render_slide(
        self,
        c: canvas.Canvas,
        slide,
        slide_w: float,
        slide_h: float,
        options: ConversionOptions,
    ) -> None:
        """Render a single PowerPoint slide onto the ReportLab canvas."""
        # 1. Background fill
        self._render_background(c, slide, slide_w, slide_h)

        # 2. Iterate and render shapes in visual order
        for shape in slide.shapes:
            try:
                self._render_shape(c, shape, slide_h, options)
            except Exception:
                # Be resilient against unexpected proprietary shape structures
                continue

    def _render_background(self, c: canvas.Canvas, slide, slide_w: float, slide_h: float) -> None:
        """Render slide background."""
        bg_color = white
        try:
            background = slide.background
            fill = background.fill
            if fill.type == 1:  # Solid fill
                rgb = fill.fore_color.rgb
                bg_color = Color(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
        except Exception:
            bg_color = white

        c.setFillColor(bg_color)
        c.rect(0, 0, slide_w, slide_h, fill=1, stroke=0)

    def _render_shape(
        self,
        c: canvas.Canvas,
        shape,
        slide_h: float,
        options: ConversionOptions,
    ) -> None:
        """Render an individual shape on the slide."""
        # Calculate bounding box in points
        try:
            left_pt = float(shape.left.pt)
            top_pt = float(shape.top.pt)
            w_pt = float(shape.width.pt)
            h_pt = float(shape.height.pt)
        except Exception:
            return

        # Coordinate transformation: PPTX (top-left) to ReportLab (bottom-left)
        bottom_pt = slide_h - (top_pt + h_pt)

        # 1. Pictures / Images
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(shape, "image"):
            self._render_picture(c, shape, left_pt, bottom_pt, w_pt, h_pt, options)
            return

        # 2. Tables
        if shape.has_table:
            self._render_table(c, shape, left_pt, top_pt, slide_h)
            return

        # 3. Shape Fill & Border (for geometric shapes)
        try:
            has_fill = False
            fill_color = None
            if hasattr(shape, "fill") and shape.fill.type == 1:  # Solid fill
                try:
                    rgb = shape.fill.fore_color.rgb
                    fill_color = Color(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
                    has_fill = True
                except Exception:
                    pass

            stroke_color = None
            stroke_w = 0.0
            if hasattr(shape, "line") and shape.line.color.type == 1:
                try:
                    l_rgb = shape.line.color.rgb
                    stroke_color = Color(l_rgb[0] / 255.0, l_rgb[1] / 255.0, l_rgb[2] / 255.0)
                    stroke_w = max(0.5, float(shape.line.width.pt)) if shape.line.width else 1.0
                except Exception:
                    pass

            if has_fill or stroke_color:
                c.saveState()
                if has_fill and fill_color:
                    c.setFillColor(fill_color)
                if stroke_color:
                    c.setStrokeColor(stroke_color)
                    c.setLineWidth(stroke_w)
                
                # Check for rectangle vs oval
                if shape.shape_type == MSO_SHAPE_TYPE.OVAL:
                    c.ellipse(left_pt, bottom_pt, left_pt + w_pt, bottom_pt + h_pt, fill=1 if has_fill else 0, stroke=1 if stroke_color else 0)
                else:
                    c.rect(left_pt, bottom_pt, w_pt, h_pt, fill=1 if has_fill else 0, stroke=1 if stroke_color else 0)
                c.restoreState()
        except Exception:
            pass

        # 4. Text frames
        if shape.has_text_frame:
            self._render_text_frame(c, shape.text_frame, left_pt, top_pt, w_pt, h_pt, slide_h)

    def _render_picture(
        self,
        c: canvas.Canvas,
        shape,
        left_pt: float,
        bottom_pt: float,
        w_pt: float,
        h_pt: float,
        options: ConversionOptions,
    ) -> None:
        """Render embedded image with optional compression."""
        try:
            image_bytes = shape.image.blob
            pil_img = Image.open(io.BytesIO(image_bytes))

            # Quality compression if requested
            if options.quality == PDFQuality.COMPRESSED and (pil_img.width > 1200 or pil_img.height > 1200):
                pil_img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                if pil_img.mode in ("RGBA", "P"):
                    pil_img.save(buf, format="PNG", optimize=True)
                else:
                    pil_img.convert("RGB").save(buf, format="JPEG", quality=75, optimize=True)
                buf.seek(0)
                img_reader = ImageReader(buf)
            else:
                img_reader = ImageReader(io.BytesIO(image_bytes))

            c.drawImage(
                img_reader,
                left_pt,
                bottom_pt,
                width=w_pt,
                height=h_pt,
                mask="auto",
                preserveAspectRatio=False,
            )
        except Exception:
            pass

    def _render_table(
        self,
        c: canvas.Canvas,
        shape,
        left_pt: float,
        top_pt: float,
        slide_h: float,
    ) -> None:
        """Render PowerPoint tables."""
        table = shape.table
        cur_y = top_pt

        for row in table.rows:
            cur_x = left_pt
            row_h = float(row.height.pt) if row.height else 24.0

            for col_idx, cell in enumerate(row.cells):
                col_w = float(table.columns[col_idx].width.pt) if table.columns[col_idx].width else 80.0
                cell_bottom = slide_h - (cur_y + row_h)

                # Draw cell border
                c.saveState()
                c.setStrokeColor(HexColor("#CCCCCC"))
                c.setLineWidth(0.5)

                # Check cell fill
                try:
                    if cell.fill.type == 1:
                        rgb = cell.fill.fore_color.rgb
                        c.setFillColor(Color(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0))
                        c.rect(cur_x, cell_bottom, col_w, row_h, fill=1, stroke=1)
                    else:
                        c.rect(cur_x, cell_bottom, col_w, row_h, fill=0, stroke=1)
                except Exception:
                    c.rect(cur_x, cell_bottom, col_w, row_h, fill=0, stroke=1)
                c.restoreState()

                # Render cell text
                if cell.text_frame and cell.text_frame.text.strip():
                    self._render_text_frame(
                        c, cell.text_frame, cur_x + 4, cur_y + 4, col_w - 8, row_h - 8, slide_h
                    )

                cur_x += col_w
            cur_y += row_h

    def _render_text_frame(
        self,
        c: canvas.Canvas,
        text_frame,
        box_left: float,
        box_top: float,
        box_w: float,
        box_h: float,
        slide_h: float,
    ) -> None:
        """Render text frames with runs, colors, fonts, and word-wrap."""
        if not text_frame.text.strip():
            return

        current_y = box_top + 4.0  # Top padding

        for paragraph in text_frame.paragraphs:
            if not paragraph.text.strip() and not paragraph.runs:
                current_y += 14.0
                continue

            align = paragraph.alignment or PP_ALIGN.LEFT
            bullet_prefix = ""
            if paragraph.level and paragraph.level > 0:
                bullet_prefix = "  " * paragraph.level + "• "

            # Default font specs for this paragraph
            default_font = "Helvetica"
            default_size = 14.0
            default_color = black

            for run in paragraph.runs:
                text_content = (bullet_prefix + run.text) if bullet_prefix else run.text
                if not text_content:
                    continue
                bullet_prefix = ""  # Only apply once to the first run of the paragraph

                # Font styling
                is_bold = bool(run.font.bold)
                is_italic = bool(run.font.italic)

                if is_bold and is_italic:
                    font_name = "Helvetica-BoldOblique"
                elif is_bold:
                    font_name = "Helvetica-Bold"
                elif is_italic:
                    font_name = "Helvetica-Oblique"
                else:
                    font_name = default_font

                font_size = float(run.font.size.pt) if run.font.size else default_size
                font_size = max(6.0, min(72.0, font_size))  # Safe bounds

                # Font color
                run_color = default_color
                try:
                    if run.font.color and run.font.color.type == 1:
                        rgb = run.font.color.rgb
                        run_color = Color(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
                except Exception:
                    run_color = default_color

                c.saveState()
                c.setFont(font_name, font_size)
                c.setFillColor(run_color)

                # Word wrapping within bounding box
                words = text_content.split(" ")
                current_line = ""
                line_height = font_size * 1.25

                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    text_width = c.stringWidth(test_line, font_name, font_size)

                    if text_width <= max(box_w, 20.0):
                        current_line = test_line
                    else:
                        # Draw current line
                        if current_line:
                            line_y = slide_h - current_y - font_size
                            self._draw_aligned_line(c, current_line, box_left, line_y, box_w, align, font_name, font_size)
                            current_y += line_height
                        current_line = word

                if current_line:
                    line_y = slide_h - current_y - font_size
                    self._draw_aligned_line(c, current_line, box_left, line_y, box_w, align, font_name, font_size)
                    current_y += line_height

                c.restoreState()

            # Space after paragraph
            space_after = float(paragraph.space_after.pt) if paragraph.space_after else 4.0
            current_y += space_after

    def _draw_aligned_line(
        self,
        c: canvas.Canvas,
        text: str,
        box_left: float,
        y: float,
        box_w: float,
        align: PP_ALIGN,
        font_name: str,
        font_size: float,
    ) -> None:
        """Draw a single line of text with alignment."""
        try:
            line_w = c.stringWidth(text, font_name, font_size)
            if align == PP_ALIGN.CENTER:
                x = box_left + max(0.0, (box_w - line_w) / 2.0)
            elif align == PP_ALIGN.RIGHT:
                x = box_left + max(0.0, box_w - line_w)
            else:
                x = box_left

            c.drawString(x, y, text)
        except Exception:
            pass
