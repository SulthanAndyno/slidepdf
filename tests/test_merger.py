"""Tests for PDF merging."""

from pathlib import Path
from pypdf import PdfReader

from slidepdf.core.engines.native import NativePythonEngine
from slidepdf.core.merger import PDFMergerUtil
from slidepdf.core.models import ConversionJob, ConversionOptions


def test_pdf_merger(tmp_path: Path):
    sample1 = Path("samples/sample_presentation.pptx")
    sample2 = Path("samples/sample_appendix.pptx")

    pdf1 = tmp_path / "doc1.pdf"
    pdf2 = tmp_path / "doc2.pdf"

    engine = NativePythonEngine()
    engine.convert(ConversionJob(input_path=sample1, output_path=pdf1), ConversionOptions())
    engine.convert(ConversionJob(input_path=sample2, output_path=pdf2), ConversionOptions())

    merged_out = tmp_path / "master_merged.pdf"
    res = PDFMergerUtil.merge_pdfs([pdf1, pdf2], merged_out)

    assert res.exists()
    reader = PdfReader(str(res))
    assert len(reader.pages) == 5  # 4 + 1
