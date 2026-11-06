"""Data models for SlidePDF Studio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class EngineType(str, Enum):
    """Available conversion engines."""
    AUTO = "auto"
    LIBREOFFICE = "libreoffice"
    MSOFFICE = "msoffice"
    NATIVE = "native"

    @classmethod
    def from_string(cls, val: str) -> "EngineType":
        val_lower = val.strip().lower()
        for member in cls:
            if member.value == val_lower:
                return member
        return cls.AUTO


class JobStatus(str, Enum):
    """Status of a conversion job."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PDFQuality(str, Enum):
    """PDF output quality."""
    STANDARD = "standard"        # Full resolution, lossless
    COMPRESSED = "compressed"    # Optimized images for smaller file size


@dataclass
class ConversionOptions:
    """Options controlling the conversion process."""
    output_dir: Optional[Path] = None
    engine: EngineType = EngineType.AUTO
    quality: PDFQuality = PDFQuality.STANDARD
    slide_range: Optional[str] = None  # e.g., "1-5, 8, 10-12"
    merge_all: bool = False
    merge_filename: str = "merged_presentation.pdf"
    prefix: str = ""
    suffix: str = ""
    overwrite: bool = True
    open_after_conversion: bool = False
    open_folder_after: bool = False
    # Post-processing enhancements
    watermark_text: Optional[str] = None
    watermark_opacity: float = 0.2
    password: Optional[str] = None
    handout_mode: int = 1  # 1 (Normal 1-up), 2 (2-up Handout), 4 (4-up Handout)
    page_numbers: bool = False
    page_number_format: str = "Page {n} of {total}"


@dataclass
class ConversionJob:
    """Represents an individual file conversion task."""
    input_path: Path
    output_path: Optional[Path] = None
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    total_slides: int = 0
    slides_to_convert: List[int] = field(default_factory=list)
    file_size_bytes: int = 0
    engine_used: Optional[EngineType] = None
    error_message: Optional[str] = None
    elapsed_seconds: float = 0.0

    def __post_init__(self):
        self.input_path = Path(self.input_path)
        if self.output_path:
            self.output_path = Path(self.output_path)
        if self.input_path.exists() and self.file_size_bytes == 0:
            self.file_size_bytes = self.input_path.stat().st_size

    @property
    def file_name(self) -> str:
        return self.input_path.name

    @property
    def formatted_size(self) -> str:
        size = self.file_size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


@dataclass
class BatchResult:
    """Summary result of a batch conversion run."""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    merged_pdf_path: Optional[Path] = None
    jobs: List[ConversionJob] = field(default_factory=list)
    total_elapsed_seconds: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.failed_jobs == 0 and self.completed_jobs > 0
