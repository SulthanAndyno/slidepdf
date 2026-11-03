"""Utility functions for SlidePDF Studio."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple


SUPPORTED_PRESENTATION_EXTENSIONS = (
    ".pptx", ".ppt", ".pptm", ".ppsx", ".pps", ".potx", ".pot", ".odp"
)

SUPPORTED_IMAGE_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"
)

SUPPORTED_DOCUMENT_EXTENSIONS = (
    ".docx", ".doc", ".odt", ".rtf", ".txt"
)

ALL_SUPPORTED_EXTENSIONS = (
    SUPPORTED_PRESENTATION_EXTENSIONS +
    SUPPORTED_IMAGE_EXTENSIONS +
    SUPPORTED_DOCUMENT_EXTENSIONS
)


def parse_slide_range(range_str: Optional[str], total_slides: int) -> List[int]:
    """Parse a slide range string (e.g. '1-3, 5, 8-10') into sorted 1-based slide indices.
    
    If range_str is empty or None, returns all slides from 1 to total_slides.
    """
    if not range_str or not range_str.strip():
        return list(range(1, total_slides + 1)) if total_slides > 0 else []

    selected_indices: Set[int] = set()
    parts = [p.strip() for p in range_str.split(",") if p.strip()]

    for part in parts:
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) == 2:
                try:
                    start = int(bounds[0].strip()) if bounds[0].strip() else 1
                    end = int(bounds[1].strip()) if bounds[1].strip() else total_slides
                    start = max(1, start)
                    if total_slides > 0:
                        end = min(total_slides, end)
                    if start <= end:
                        selected_indices.update(range(start, end + 1))
                except ValueError:
                    continue
        else:
            try:
                slide_num = int(part)
                if total_slides > 0:
                    if 1 <= slide_num <= total_slides:
                        selected_indices.add(slide_num)
                else:
                    if slide_num >= 1:
                        selected_indices.add(slide_num)
            except ValueError:
                continue

    return sorted(list(selected_indices))


def inspect_pptx(file_path: Path) -> Tuple[int, Optional[str]]:
    """Inspect a presentation, document, or image file to determine slide count and title.
    
    Returns (slide_count, title_or_none).
    """
    ext = file_path.suffix.lower()

    # Images
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return 1, file_path.stem

    # OpenDocument Presentation (.odp)
    if ext == ".odp":
        try:
            import zipfile
            with zipfile.ZipFile(str(file_path), "r") as z:
                if "content.xml" in z.namelist():
                    content = z.read("content.xml").decode("utf-8", errors="ignore")
                    # Count <draw:page elements
                    count = content.count("<draw:page ")
                    return max(1, count), file_path.stem
        except Exception:
            return 1, file_path.stem

    # PowerPoint / OpenXML (.pptx, .pptm, .potx, .ppsx)
    try:
        from pptx import Presentation
        prs = Presentation(str(file_path))
        slide_count = len(prs.slides)
        title = None
        if slide_count > 0:
            first_slide = prs.slides[0]
            for shape in first_slide.shapes:
                if shape.has_text_frame and shape.text_frame.text.strip():
                    title = shape.text_frame.text.strip().split("\n")[0]
                    break
        return slide_count, title
    except Exception:
        # Fallback inspection via ZIP XML if python-pptx hits issues
        try:
            import zipfile
            with zipfile.ZipFile(str(file_path), 'r') as z:
                slide_files = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
                if slide_files:
                    return len(slide_files), file_path.stem
        except Exception:
            pass

    return 0, file_path.stem


def get_default_output_path(
    input_path: Path,
    output_dir: Optional[Path] = None,
    prefix: str = "",
    suffix: str = ""
) -> Path:
    """Generate the target PDF output path."""
    dest_dir = output_dir if output_dir else input_path.parent
    base_stem = input_path.stem
    new_name = f"{prefix}{base_stem}{suffix}.pdf"
    return dest_dir / new_name


def open_file_in_system_viewer(file_path: Path) -> bool:
    """Open a file (e.g. PDF) in the operating system's default viewer."""
    path_str = str(file_path.resolve())
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path_str)  # type: ignore[attr-defined]
            return True
        elif system == "Darwin":
            subprocess.Popen(["open", path_str])
            return True
        else:  # Linux / Unix
            subprocess.Popen(["xdg-open", path_str])
            return True
    except Exception:
        return False


def open_folder_in_file_manager(folder_path: Path) -> bool:
    """Open a directory in the operating system's file manager."""
    path_str = str(folder_path.resolve())
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(["explorer", path_str])
            return True
        elif system == "Darwin":
            subprocess.Popen(["open", path_str])
            return True
        else:  # Linux / Unix
            subprocess.Popen(["xdg-open", path_str])
            return True
    except Exception:
        return False
