"""Utility functions for SlidePDF Studio with hardened security controls."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Security limits
MAX_PARSED_SLIDES = 10000
MAX_SAFE_XML_SIZE = 50 * 1024 * 1024  # 50 MB max uncompressed XML
MAX_ZIP_ENTRIES = 5000                 # max entries in archive

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


def sanitize_filename_component(name: Optional[str]) -> str:
    """Sanitize a filename component, removing path traversal tokens and illegal characters."""
    if not name:
        return ""
    # Strip null bytes and control characters
    name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", str(name))
    # Strip directory separators and traversal tokens
    name = re.sub(r"[/\\]+", "", name)
    name = name.replace("..", "")
    # Remove leading dots or dashes that might be parsed as flags
    name = name.lstrip(".-").strip()
    return name


def parse_slide_range(range_str: Optional[str], total_slides: int) -> List[int]:
    """Parse a slide range string (e.g. '1-3, 5, 8-10') into sorted 1-based slide indices.
    
    If range_str is empty or None, returns all slides from 1 to total_slides.
    Protected against integer overflow, negative values, and memory exhaustion DoS.
    """
    effective_max = min(total_slides, MAX_PARSED_SLIDES) if total_slides > 0 else MAX_PARSED_SLIDES
    if range_str is None or not range_str.strip():
        return list(range(1, effective_max + 1)) if total_slides > 0 else []

    selected_indices: Set[int] = set()
    parts = [p.strip() for p in range_str.split(",") if p.strip()]

    for part in parts:
        # Check if part is a range "start-end" (avoid negative numbers like "-5")
        if "-" in part and not part.startswith("-"):
            bounds = part.split("-")
            if len(bounds) == 2 and bounds[0].strip():
                try:
                    start_str = bounds[0].strip()
                    end_str = bounds[1].strip()
                    start = int(start_str)
                    end = int(end_str) if end_str else effective_max
                    if start < 1 or end < 1:
                        continue
                    start = max(1, start)
                    end = min(end, effective_max)
                    # Protect against massive ranges that exhaust RAM
                    if start <= end and (end - start) <= MAX_PARSED_SLIDES:
                        selected_indices.update(range(start, end + 1))
                except (ValueError, OverflowError):
                    continue
        else:
            try:
                slide_num = int(part)
                if 1 <= slide_num <= effective_max:
                    selected_indices.add(slide_num)
            except (ValueError, OverflowError):
                continue

    return sorted(list(selected_indices))


def inspect_pptx(file_path: Path) -> Tuple[int, Optional[str]]:
    """Inspect a presentation, document, or image file to determine slide count and title.
    
    Includes safety checks against zip bombs and decompression bombs.
    Returns (slide_count, title_or_none).
    """
    if not file_path.exists() or not file_path.is_file():
        return 0, None

    if file_path.stat().st_size == 0:
        return 0, None

    ext = file_path.suffix.lower()

    # Images
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return 1, sanitize_filename_component(file_path.stem)

    # OpenDocument Presentation (.odp)
    if ext == ".odp":
        try:
            import zipfile
            with zipfile.ZipFile(str(file_path), "r") as z:
                namelist = z.namelist()
                if len(namelist) > MAX_ZIP_ENTRIES:
                    return 1, file_path.stem
                if "content.xml" in namelist:
                    info = z.getinfo("content.xml")
                    if info.file_size > MAX_SAFE_XML_SIZE:
                        # Reject oversized XML stream
                        return 1, file_path.stem
                    with z.open("content.xml") as f:
                        raw_bytes = f.read(MAX_SAFE_XML_SIZE)
                        content = raw_bytes.decode("utf-8", errors="ignore")
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
                    raw_title = shape.text_frame.text.strip().split("\n")[0]
                    title = sanitize_filename_component(raw_title)
                    break
        return min(slide_count, MAX_PARSED_SLIDES), title
    except Exception:
        # Fallback inspection via ZIP XML if python-pptx hits issues
        try:
            import zipfile
            with zipfile.ZipFile(str(file_path), 'r') as z:
                namelist = z.namelist()
                if len(namelist) <= MAX_ZIP_ENTRIES:
                    slide_files = [n for n in namelist if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
                    if slide_files:
                        return min(len(slide_files), MAX_PARSED_SLIDES), file_path.stem
        except Exception:
            pass

    return 0, file_path.stem


def get_default_output_path(
    input_path: Path,
    output_dir: Optional[Path] = None,
    prefix: str = "",
    suffix: str = "",
) -> Path:
    """Generate the target PDF output path safely preventing directory traversal (CWE-22)."""
    dest_dir = (output_dir if output_dir else input_path.parent).resolve()
    clean_prefix = sanitize_filename_component(prefix)
    clean_suffix = sanitize_filename_component(suffix)
    clean_stem = sanitize_filename_component(input_path.stem) or "presentation"

    new_name = f"{clean_prefix}{clean_stem}{clean_suffix}.pdf"
    target = (dest_dir / new_name).resolve()

    # Ensure target path does not escape dest_dir
    try:
        target.relative_to(dest_dir)
    except ValueError:
        target = dest_dir / f"{clean_stem}.pdf"

    return target


def open_file_in_system_viewer(file_path: Path) -> bool:
    """Open a file (e.g. PDF) safely in the operating system's default viewer."""
    try:
        resolved = file_path.resolve()
        if not resolved.is_file():
            return False

        path_str = str(resolved)
        system = platform.system()

        if system == "Windows":
            os.startfile(path_str)  # type: ignore[attr-defined]
            return True
        elif system == "Darwin":
            open_bin = shutil.which("open")
            if open_bin:
                subprocess.Popen([open_bin, "--", path_str])  # nosec B603
                return True
        else:  # Linux / Unix
            xdg_bin = shutil.which("xdg-open")
            if xdg_bin:
                subprocess.Popen([xdg_bin, "--", path_str])  # nosec B603
                return True
    except Exception:
        return False
    return False


def open_folder_in_file_manager(folder_path: Path) -> bool:
    """Open a directory safely in the operating system's file manager."""
    try:
        resolved = folder_path.resolve()
        if not resolved.is_dir():
            return False

        path_str = str(resolved)
        system = platform.system()

        if system == "Windows":
            explorer_bin = shutil.which("explorer")
            if explorer_bin:
                subprocess.Popen([explorer_bin, path_str])  # nosec B603
                return True
        elif system == "Darwin":
            open_bin = shutil.which("open")
            if open_bin:
                subprocess.Popen([open_bin, "--", path_str])  # nosec B603
                return True
        else:  # Linux / Unix
            xdg_bin = shutil.which("xdg-open")
            if xdg_bin:
                subprocess.Popen([xdg_bin, "--", path_str])  # nosec B603
                return True
    except Exception:
        return False
    return False
