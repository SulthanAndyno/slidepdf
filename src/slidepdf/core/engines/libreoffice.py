"""LibreOffice / OpenOffice headless conversion engine."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional

from slidepdf.core.engines.base import BaseEngine
from slidepdf.core.models import ConversionJob, ConversionOptions, EngineType
from slidepdf.core.utils import get_default_output_path, inspect_pptx, parse_slide_range


class LibreOfficeEngine(BaseEngine):
    """Converts presentations via LibreOffice headless CLI."""

    def __init__(self):
        self._binary_path: Optional[str] = self._find_binary()

    @property
    def name(self) -> str:
        return "LibreOffice Engine (Headless)"

    @property
    def engine_type(self) -> EngineType:
        return EngineType.LIBREOFFICE

    def is_available(self) -> bool:
        return self._binary_path is not None and os.path.exists(self._binary_path)

    def get_details(self) -> str:
        if not self.is_available():
            return "Not found on this system. Install LibreOffice to enable high-fidelity vector conversion."
        try:
            res = subprocess.run([self._binary_path, "--version"], capture_output=True, text=True, timeout=5)
            version_str = res.stdout.strip() if res.returncode == 0 else "Unknown version"
            return f"{version_str} ({self._binary_path})"
        except Exception:
            return f"Found at: {self._binary_path}"

    def _find_binary(self) -> Optional[str]:
        """Locate soffice or libreoffice executable across operating systems."""
        # Check PATH first
        for name in ["soffice", "libreoffice"]:
            found = shutil.which(name)
            if found:
                return found

        system = platform.system()
        candidates: List[str] = []

        if system == "Linux":
            candidates = [
                "/usr/bin/soffice",
                "/usr/bin/libreoffice",
                "/usr/lib/libreoffice/program/soffice",
                "/usr/local/bin/soffice",
                "/snap/bin/libreoffice",
                "/var/lib/flatpak/exports/bin/org.libreoffice.LibreOffice",
            ]
        elif system == "Darwin":  # macOS
            candidates = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/usr/local/bin/soffice",
            ]
        elif system == "Windows":
            for env_var in ["PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"]:
                base = os.environ.get(env_var)
                if base:
                    candidates.append(os.path.join(base, "LibreOffice", "program", "soffice.exe"))

        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def convert(
        self,
        job: ConversionJob,
        options: ConversionOptions,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        if not self.is_available() or not self._binary_path:
            raise RuntimeError(
                "LibreOffice executable was not detected on this system. "
                "Please install LibreOffice or switch to the Native Python engine."
            )

        input_path = job.input_path
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Final target output path
        output_path = job.output_path or get_default_output_path(
            input_path,
            output_dir=options.output_dir,
            prefix=options.prefix,
            suffix=options.suffix,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_callback:
            progress_callback(0.15, "Starting LibreOffice headless daemon...")

        # Use an isolated temporary directory for the conversion
        with tempfile.TemporaryDirectory(prefix="slidepdf_lo_") as tmp_dir:
            tmp_out_dir = Path(tmp_dir) / "output"
            tmp_out_dir.mkdir(parents=True, exist_ok=True)
            tmp_profile_dir = Path(tmp_dir) / "profile"
            tmp_profile_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                self._binary_path,
                "--headless",
                "--invisible",
                "--nologo",
                "--nodefault",
                f"-env:UserInstallation={tmp_profile_dir.as_uri()}",
                "--convert-to",
                "pdf",
                "--",
                str(input_path.resolve()),
                "--outdir",
                str(tmp_out_dir.resolve()),
            ]

            if progress_callback:
                progress_callback(0.35, "Rendering PowerPoint slides to PDF vector...")

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=180,  # 3 minutes maximum timeout
                )
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError("LibreOffice conversion timed out after 180 seconds.") from exc

            if proc.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice failed (code {proc.returncode}): {proc.stderr or proc.stdout}"
                )

            # Find generated PDF in temp dir
            expected_pdf = tmp_out_dir / f"{input_path.stem}.pdf"
            if not expected_pdf.exists():
                # Fallback: find any .pdf in the temp dir
                pdfs = list(tmp_out_dir.glob("*.pdf"))
                if pdfs:
                    expected_pdf = pdfs[0]
                else:
                    raise FileNotFoundError(
                        f"LibreOffice finished, but no PDF was generated: {proc.stdout}\n{proc.stderr}"
                    )

            if progress_callback:
                progress_callback(0.80, "Processing output pages and slide ranges...")

            # If slide ranges are specified, filter pages with pypdf
            total_slides, _ = inspect_pptx(input_path)
            target_indices = parse_slide_range(options.slide_range, total_slides)

            if options.slide_range and target_indices and len(target_indices) < total_slides:
                from pypdf import PdfReader, PdfWriter

                reader = PdfReader(str(expected_pdf))
                writer = PdfWriter()
                for slide_idx in target_indices:
                    page_zero_indexed = slide_idx - 1
                    if 0 <= page_zero_indexed < len(reader.pages):
                        writer.add_page(reader.pages[page_zero_indexed])

                with open(output_path, "wb") as f_out:
                    writer.write(f_out)
            else:
                shutil.copy2(expected_pdf, output_path)

        if progress_callback:
            progress_callback(1.0, "Conversion completed.")

        job.output_path = output_path
        return output_path
