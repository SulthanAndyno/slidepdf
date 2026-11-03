"""Tests for Native Python PPTX to PDF conversion."""

from pathlib import Path
from pypdf import PdfReader

from slidepdf.core.engines.native import NativePythonEngine
from slidepdf.core.models import ConversionJob, ConversionOptions, PDFQuality


def test_native_converter_full_presentation(tmp_path: Path):
    sample_pptx = Path("samples/sample_presentation.pptx")
    if not sample_pptx.exists():
        # Generate if needed
        from scripts.generate_sample_pptx import generate_presentations
        generate_presentations(Path("samples"))

    target_pdf = tmp_path / "converted.pdf"
    job = ConversionJob(input_path=sample_pptx, output_path=target_pdf)
    options = ConversionOptions()

    engine = NativePythonEngine()
    result_path = engine.convert(job, options)

    assert result_path.exists()
    assert result_path == target_pdf

    # Verify PDF content and page count
    reader = PdfReader(str(result_path))
    assert len(reader.pages) == 4


def test_native_converter_slide_range(tmp_path: Path):
    sample_pptx = Path("samples/sample_presentation.pptx")
    target_pdf = tmp_path / "range_test.pdf"
    job = ConversionJob(input_path=sample_pptx, output_path=target_pdf)
    options = ConversionOptions(slide_range="1, 3")

    engine = NativePythonEngine()
    result_path = engine.convert(job, options)

    assert result_path.exists()
    reader = PdfReader(str(result_path))
    assert len(reader.pages) == 2


def test_native_converter_compression(tmp_path: Path):
    sample_pptx = Path("samples/sample_presentation.pptx")
    std_pdf = tmp_path / "standard.pdf"
    comp_pdf = tmp_path / "compressed.pdf"

    engine = NativePythonEngine()

    job1 = ConversionJob(input_path=sample_pptx, output_path=std_pdf)
    engine.convert(job1, ConversionOptions(quality=PDFQuality.STANDARD))

    job2 = ConversionJob(input_path=sample_pptx, output_path=comp_pdf)
    engine.convert(job2, ConversionOptions(quality=PDFQuality.COMPRESSED))

    assert std_pdf.exists()
    assert comp_pdf.exists()


def test_native_converter_image(tmp_path: Path):
    icon_path = Path("assets/icon.png")
    out_pdf = tmp_path / "from_image.pdf"
    engine = NativePythonEngine()
    job = ConversionJob(input_path=icon_path, output_path=out_pdf)

    res = engine.convert(job, ConversionOptions())
    assert res.exists()
    reader = PdfReader(str(res))
    assert len(reader.pages) == 1
