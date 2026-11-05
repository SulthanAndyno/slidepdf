"""PDF merging and post-processing utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, List, Optional

from pypdf import PdfReader, PdfWriter


class PDFMergerUtil:
    """Combines multiple PDF files into a single master PDF document."""

    @staticmethod
    def merge_pdfs(
        pdf_paths: List[Path],
        output_path: Path,
        add_bookmarks: bool = True,
        title: str = "Merged Presentations",
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        """Merge a sequence of PDF files into a single output PDF.
        
        Args:
            pdf_paths: List of input PDF file paths.
            output_path: Target merged PDF file path.
            add_bookmarks: Whether to create PDF bookmarks for each input presentation.
            title: Metadata document title.
            progress_callback: Optional progress reporter (0.0 to 1.0).
            
        Returns:
            The Path to the resulting merged PDF file.
        """
        valid_pdfs = [p for p in pdf_paths if p.exists() and p.stat().st_size > 0]
        if not valid_pdfs:
            raise ValueError("No valid PDF files provided for merging.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()

        total = len(valid_pdfs)
        for idx, pdf in enumerate(valid_pdfs, start=1):
            if progress_callback:
                progress_callback(
                    (idx - 1) / total,
                    f"Merging ({idx}/{total}): {pdf.name}...",
                )

            # Use presentation stem as the bookmark title (sanitized)
            bookmark_title = (
                re.sub(r"[\x00-\x1f\x7f-\x9f]", "", pdf.stem).strip()
                if add_bookmarks
                else None
            )
            writer.append(str(pdf), outline_item=bookmark_title)

        if progress_callback:
            progress_callback(0.95, "Writing merged PDF file to disk...")

        # Add sanitized document metadata
        clean_title = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", title).strip() or "Merged Presentations"
        writer.add_metadata({
            "/Title": clean_title,
            "/Producer": "SlidePDF Studio",
            "/Creator": "SlidePDF Studio PDF Merger",
        })

        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        writer.close()

        if progress_callback:
            progress_callback(1.0, f"Merged {total} files successfully.")

        return output_path
