"""Engine detection, registration, and health diagnostics."""

from __future__ import annotations

import platform
import sys
from typing import Dict, List, Optional, Tuple

from slidepdf.core.engines.base import BaseEngine
from slidepdf.core.engines.libreoffice import LibreOfficeEngine
from slidepdf.core.engines.msoffice import MSOfficeEngine
from slidepdf.core.engines.native import NativePythonEngine
from slidepdf.core.models import EngineType


class EngineDetector:
    """Manages conversion engine discovery and selection."""

    def __init__(self):
        self._native_engine = NativePythonEngine()
        self._libreoffice_engine = LibreOfficeEngine()
        self._msoffice_engine = MSOfficeEngine()

        self._engines: Dict[EngineType, BaseEngine] = {
            EngineType.NATIVE: self._native_engine,
            EngineType.LIBREOFFICE: self._libreoffice_engine,
            EngineType.MSOFFICE: self._msoffice_engine,
        }

    def get_engine(self, engine_type: EngineType = EngineType.AUTO) -> BaseEngine:
        """Resolve the requested engine or select the optimal auto engine."""
        if engine_type == EngineType.AUTO:
            return self.get_best_engine()

        if engine_type in self._engines:
            engine = self._engines[engine_type]
            if not engine.is_available():
                raise RuntimeError(
                    f"Selected engine '{engine.name}' is not available on this system. "
                    f"Details: {engine.get_details()}"
                )
            return engine

        raise ValueError(f"Unknown engine type: {engine_type}")

    def get_best_engine(self) -> BaseEngine:
        """Automatically select the best available engine for the current platform."""
        # 1. On Windows, if MS Office PowerPoint is installed, prefer it
        if sys.platform == "win32" and self._msoffice_engine.is_available():
            return self._msoffice_engine

        # 2. LibreOffice (cross-platform, industry standard high fidelity)
        if self._libreoffice_engine.is_available():
            return self._libreoffice_engine

        # 3. Native pure-Python fallback (always available)
        return self._native_engine

    def list_available_engines(self) -> List[Tuple[EngineType, BaseEngine, bool]]:
        """List all engines with their availability status."""
        results = []
        for etype, engine in self._engines.items():
            results.append((etype, engine, engine.is_available()))
        return results

    def diagnose_system(self) -> Dict[str, str]:
        """Produce a comprehensive system diagnostic report."""
        best = self.get_best_engine()
        return {
            "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "python": platform.python_version(),
            "best_engine": f"{best.name} ({best.engine_type.value})",
            "native_status": "Available (Bundled)",
            "native_details": self._native_engine.get_details(),
            "libreoffice_status": "Available" if self._libreoffice_engine.is_available() else "Not Found",
            "libreoffice_details": self._libreoffice_engine.get_details(),
            "msoffice_status": "Available" if self._msoffice_engine.is_available() else "Not Found / Unsupported OS",
            "msoffice_details": self._msoffice_engine.get_details(),
        }
