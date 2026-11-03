"""Tests for data models in SlidePDF Studio."""

from pathlib import Path
from slidepdf.core.models import (
    ConversionJob,
    ConversionOptions,
    EngineType,
    JobStatus,
    PDFQuality,
)


def test_engine_type_from_string():
    assert EngineType.from_string("native") == EngineType.NATIVE
    assert EngineType.from_string("libreoffice") == EngineType.LIBREOFFICE
    assert EngineType.from_string("msoffice") == EngineType.MSOFFICE
    assert EngineType.from_string("auto") == EngineType.AUTO
    assert EngineType.from_string("UNKNOWN") == EngineType.AUTO


def test_conversion_job_formatting(tmp_path: Path):
    dummy_file = tmp_path / "test.pptx"
    dummy_file.write_bytes(b"0" * 2048)  # 2 KB

    job = ConversionJob(input_path=dummy_file)
    assert job.file_name == "test.pptx"
    assert "KB" in job.formatted_size
    assert job.status == JobStatus.PENDING
    assert job.progress == 0.0


def test_conversion_options_defaults():
    opts = ConversionOptions()
    assert opts.engine == EngineType.AUTO
    assert opts.quality == PDFQuality.STANDARD
    assert opts.merge_all is False
    assert opts.slide_range is None
