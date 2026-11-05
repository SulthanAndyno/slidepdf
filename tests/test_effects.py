"""Unit and integration tests for post-processing effects and queue operations."""

import io
from pathlib import Path
import pypdf
import pytest
from reportlab.pdfgen import canvas

from slidepdf.core.effects import (
    apply_encryption,
    apply_post_processing,
    apply_watermark,
    create_handout,
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

    # Mock tkinter frame without displaying window
    import customtkinter as ctk
    root = ctk.CTk()
    root.withdraw()

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
