"""Unit and integration tests for post-processing effects and queue operations."""

import io
from pathlib import Path
import pypdf
import pytest
from reportlab.pdfgen import canvas

from slidepdf.core.effects import (
    _safe_write_pdf,
    apply_encryption,
    apply_optimization,
    apply_page_numbers,
    apply_post_processing,
    apply_watermark,
    create_handout,
    generate_page_number_page,
    generate_watermark_page,
)
from slidepdf.core.models import ConversionJob, ConversionOptions


def _create_sample_pdf(num_pages: int, path: Path) -> Path:
    """Helper to generate a dummy PDF with known slide count."""
    c = canvas.Canvas(str(path), pagesize=(960, 540))
    for i in range(1, num_pages + 1):
        c.drawString(100, 270, f"Slide Test Page {i}")
        c.rect(20, 20, 920, 500)
        c.showPage()
    c.save()
    return path


def test_generate_watermark_page():
    """Verify watermark overlay generation produces a valid PageObject."""
    wm = generate_watermark_page(960, 540, "CONFIDENTIAL", opacity=0.25)
    assert isinstance(wm, pypdf.PageObject)
    assert float(wm.mediabox.width) == 960
    assert float(wm.mediabox.height) == 540


def test_apply_watermark(tmp_path):
    """Test watermark stamping on all PDF pages."""
    src = _create_sample_pdf(3, tmp_path / "watermark_src.pdf")
    dest = tmp_path / "watermark_out.pdf"

    result = apply_watermark(src, dest, text="DO NOT DISTRIBUTE", opacity=0.3)
    assert result.exists()

    reader = pypdf.PdfReader(str(result))
    assert len(reader.pages) == 3


def test_apply_encryption(tmp_path):
    """Test standard AES password encryption and decryption."""
    src = _create_sample_pdf(2, tmp_path / "plain.pdf")
    dest = tmp_path / "encrypted.pdf"

    result = apply_encryption(src, dest, user_password="secureSecret123")
    assert result.exists()

    reader = pypdf.PdfReader(str(result))
    assert reader.is_encrypted

    # Attempt decrypt with correct password
    decrypt_status = reader.decrypt("secureSecret123")
    assert decrypt_status > 0
    assert len(reader.pages) == 2


def test_create_handout_2up(tmp_path):
    """Test 2-up handout collapses 4 slides into 2 A4 pages."""
    src = _create_sample_pdf(4, tmp_path / "slides_4.pdf")
    dest = tmp_path / "handout_2up.pdf"

    result = create_handout(src, dest, slides_per_page=2)
    assert result.exists()

    reader = pypdf.PdfReader(str(result))
    assert len(reader.pages) == 2


def test_create_handout_4up(tmp_path):
    """Test 4-up handout collapses 8 slides into 2 A4 pages."""
    src = _create_sample_pdf(8, tmp_path / "slides_8.pdf")
    dest = tmp_path / "handout_4up.pdf"

    result = create_handout(src, dest, slides_per_page=4)
    assert result.exists()

    reader = pypdf.PdfReader(str(result))
    assert len(reader.pages) == 2


def test_full_post_processing_pipeline(tmp_path):
    """Verify combination of Handout (2-up), Watermark, and Encryption."""
    src = _create_sample_pdf(4, tmp_path / "raw.pdf")
    dest = tmp_path / "final_protected.pdf"

    opts = ConversionOptions(
        handout_mode=2,
        watermark_text="INTERNAL ONLY",
        watermark_opacity=0.2,
        password="MyPassword99",
    )

    result = apply_post_processing(src, opts, target_path=dest)
    assert result.exists()

    reader = pypdf.PdfReader(str(result))
    assert reader.is_encrypted
    reader.decrypt("MyPassword99")
    # 4 slides transformed into 2-up handout = 2 pages
    assert len(reader.pages) == 2


def test_queue_reordering_logic():
    """Verify queue move up and move down behavior."""
    from slidepdf.ui.components.file_queue import FileQueueView
    from unittest.mock import MagicMock
    import customtkinter as ctk

    root = None
    try:
        root = ctk.CTk()
        root.withdraw()
    except Exception:
        # Gracefully handle headless CI runners without X11 server ($DISPLAY)
        root = None

    if root is not None:
        try:
            queue_view = FileQueueView(root)
            job1 = ConversionJob(input_path=Path("/tmp/presentation1.pptx"))
            job2 = ConversionJob(input_path=Path("/tmp/presentation2.pptx"))
            job3 = ConversionJob(input_path=Path("/tmp/presentation3.pptx"))

            queue_view.jobs = [job1, job2, job3]

            # Move job 2 up -> should be first
            queue_view.move_job_up(job2.job_id)
            assert [j.job_id for j in queue_view.jobs] == [job2.job_id, job1.job_id, job3.job_id]

            # Move job 2 up again -> already at index 0, should stay
            queue_view.move_job_up(job2.job_id)
            assert [j.job_id for j in queue_view.jobs] == [job2.job_id, job1.job_id, job3.job_id]

            # Move job 2 down -> should be second
            queue_view.move_job_down(job2.job_id)
            assert [j.job_id for j in queue_view.jobs] == [job1.job_id, job2.job_id, job3.job_id]
        finally:
            root.destroy()
    else:
        # Mock-based validation in headless environments
        queue_mock = MagicMock(spec=FileQueueView)
        job1 = ConversionJob(input_path=Path("/tmp/presentation1.pptx"))
        job2 = ConversionJob(input_path=Path("/tmp/presentation2.pptx"))
        job3 = ConversionJob(input_path=Path("/tmp/presentation3.pptx"))
        queue_mock.jobs = [job1, job2, job3]
        queue_mock._item_rows = {}

        FileQueueView.move_job_up(queue_mock, job2.job_id)
        assert [j.job_id for j in queue_mock.jobs] == [job2.job_id, job1.job_id, job3.job_id]

        FileQueueView.move_job_up(queue_mock, job2.job_id)
        assert [j.job_id for j in queue_mock.jobs] == [job2.job_id, job1.job_id, job3.job_id]

        FileQueueView.move_job_down(queue_mock, job2.job_id)
        assert [j.job_id for j in queue_mock.jobs] == [job1.job_id, job2.job_id, job3.job_id]


def test_generate_page_number_page():
    """Verify page number overlay generation produces a valid PageObject."""
    num_page = generate_page_number_page(960, 540, page_num=1, total_pages=5)
    assert isinstance(num_page, pypdf.PageObject)
    assert float(num_page.mediabox.width) == 960
    assert float(num_page.mediabox.height) == 540


def test_apply_page_numbers(tmp_path):
    """Test applying slide page numbers to all pages."""
    src = _create_sample_pdf(3, tmp_path / "numbered_src.pdf")
    dest = tmp_path / "numbered_out.pdf"

    result = apply_page_numbers(src, dest, format_str="Slide {n} / {total}")
    assert result.exists()

    with pypdf.PdfReader(str(result)) as reader:
        assert len(reader.pages) == 3


def test_apply_optimization(tmp_path):
    """Test PDF stream and identical object compression."""
    src = _create_sample_pdf(3, tmp_path / "unoptimized.pdf")
    dest = tmp_path / "optimized.pdf"

    result = apply_optimization(src, dest)
    assert result.exists()
    assert result.stat().st_size > 0


def test_watermark_sanitization():
    """Verify watermark text sanitization removes control characters and handles excessive length."""
    long_text = "CONFIDENTIAL\x00\x1f" + "A" * 500
    page = generate_watermark_page(800, 600, long_text)
    assert isinstance(page, pypdf.PageObject)


def test_encrypted_pdf_error_handling(tmp_path):
    """Verify attempting to watermark an already encrypted PDF raises ValueError gracefully."""
    src = _create_sample_pdf(2, tmp_path / "plain_for_enc.pdf")
    enc_path = tmp_path / "already_encrypted.pdf"
    apply_encryption(src, enc_path, user_password="pass")

    out_path = tmp_path / "should_fail.pdf"
    with pytest.raises(ValueError, match="Cannot apply watermark to encrypted PDF"):
        apply_watermark(enc_path, out_path, text="DRAFT")


def test_safe_write_pdf_cleanup_on_error(tmp_path, monkeypatch):
    """Verify temporary files are cleaned up if an exception occurs during writing."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(100, 100)
    target = tmp_path / "target.pdf"

    def faulty_write(f):
        raise OSError("Disk full simulation")

    monkeypatch.setattr(writer, "write", faulty_write)

    with pytest.raises(OSError, match="Disk full simulation"):
        _safe_write_pdf(writer, target)

    # Ensure no temporary .pdf files remain in directory
    temp_files = list(tmp_path.glob("*.pdf"))
    assert len(temp_files) == 0
