"""Abstract Base Engine for SlidePDF Studio."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

from slidepdf.core.models import ConversionJob, ConversionOptions, EngineType


class BaseEngine(ABC):
    """Abstract base class that all conversion engines implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the engine."""
        pass

    @property
    @abstractmethod
    def engine_type(self) -> EngineType:
        """EngineType identifier."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is available on the current host system."""
        pass

    @abstractmethod
    def get_details(self) -> str:
        """Return engine version, executable path, or capability details."""
        pass

    @abstractmethod
    def convert(
        self,
        job: ConversionJob,
        options: ConversionOptions,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        """Convert the PPTX in job.input_path to PDF and return the output Path.
        
        Args:
            job: The conversion task details.
            options: Conversion configuration settings.
            progress_callback: Optional callback taking (progress: 0.0-1.0, message: str).
            
        Returns:
            The Path to the created PDF file.
            
        Raises:
            Exception if conversion fails.
        """
        pass
