"""Microsoft Office COM Automation conversion engine (Windows only)."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Callable, Optional

from slidepdf.core.engines.base import BaseEngine
from slidepdf.core.models import ConversionJob, ConversionOptions, EngineType
from slidepdf.core.utils import get_default_output_path, inspect_pptx, parse_slide_range


class MSOfficeEngine(BaseEngine):
    """Converts presentations via Microsoft PowerPoint COM automation on Windows."""

    @property
    def name(self) -> str:
        return "Microsoft Office Engine (PowerPoint COM)"

    @property
    def engine_type(self) -> EngineType:
        return EngineType.MSOFFICE

    def is_available(self) -> bool:
        if sys.platform != "win32":
            return False

        try:
            import win32com.client  # type: ignore[import-not-found]
            # Verify PowerPoint COM ProgID exists in registry
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "PowerPoint.Application"):
                return True
        except Exception:
            return False

    def get_details(self) -> str:
        if sys.platform != "win32":
            return "Not available (Windows operating system only)"
        if not self.is_available():
            return "Microsoft PowerPoint was not detected on this system"
        return "Microsoft Office PowerPoint installed (Native COM automation)"

    def convert(
        self,
        job: ConversionJob,
        options: ConversionOptions,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        if not self.is_available():
            raise RuntimeError(
                "Microsoft PowerPoint COM automation is only supported on Windows with Microsoft Office installed."
            )

        import pythoncom  # type: ignore[import-not-found]
        import win32com.client  # type: ignore[import-not-found]

        input_path = job.input_path.resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_path = (job.output_path or get_default_output_path(
            input_path,
            output_dir=options.output_dir,
            prefix=options.prefix,
            suffix=options.suffix,
        )).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_callback:
            progress_callback(0.1, "Initializing COM and PowerPoint instance...")

        # Initialize COM library for current thread
        pythoncom.CoInitialize()
        powerpoint = None
        deck = None

        try:
            # 32 = ppSaveAsPDF format in PowerPoint Object Model
            pp_save_as_pdf = 32

            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            if progress_callback:
                progress_callback(0.3, "Opening presentation...")

            deck = powerpoint.Presentations.Open(
                str(input_path),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )

            if progress_callback:
                progress_callback(0.6, "Exporting to PDF format...")

            deck.SaveAs(str(output_path), pp_save_as_pdf)

            # Slide range filtering if needed
            total_slides, _ = inspect_pptx(input_path)
            target_indices = parse_slide_range(options.slide_range, total_slides)

            if options.slide_range and target_indices and len(target_indices) < total_slides:
                if progress_callback:
                    progress_callback(0.85, "Filtering requested slide pages...")

                from pypdf import PdfReader, PdfWriter
                writer = PdfWriter()
                with PdfReader(str(output_path)) as reader:
                    for slide_idx in target_indices:
                        page_zero_indexed = slide_idx - 1
                        if 0 <= page_zero_indexed < len(reader.pages):
                            writer.add_page(reader.pages[page_zero_indexed])

                tmp_filtered = output_path.parent / f".tmp_{output_path.name}"
                try:
                    with open(tmp_filtered, "wb") as f_out:
                        writer.write(f_out)
                    tmp_filtered.replace(output_path)
                finally:
                    if tmp_filtered.exists():
                        tmp_filtered.unlink(missing_ok=True)

        finally:
            if deck is not None:
                try:
                    deck.Close()
                except Exception:
                    pass
            if powerpoint is not None:
                try:
                    powerpoint.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()

        if progress_callback:
            progress_callback(1.0, "Conversion completed.")

        job.output_path = output_path
        return output_path
