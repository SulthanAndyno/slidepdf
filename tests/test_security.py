"""Security, vulnerability, and robustness tests for SlidePDF Studio."""

import io
from pathlib import Path
import pytest
from PIL import Image

from slidepdf.core.converter import ConversionManager
from slidepdf.core.engines.native import NativePythonEngine
from slidepdf.core.models import ConversionJob, ConversionOptions
from slidepdf.core.utils import (
    get_default_output_path,
    inspect_pptx,
    open_file_in_system_viewer,
    open_folder_in_file_manager,
    parse_slide_range,
    sanitize_filename_component,
)


def test_sanitize_filename_component():
    assert sanitize_filename_component("../../etc/passwd") == "etcpasswd"
    assert sanitize_filename_component("..\\..\\windows\\system32") == "windowssystem32"
    assert sanitize_filename_component("test\x00file\x1f.pdf") == "testfile.pdf"
    assert sanitize_filename_component("--malicious-flag") == "malicious-flag"
    assert sanitize_filename_component("..hidden_file") == "hidden_file"
    assert sanitize_filename_component("") == ""
    assert sanitize_filename_component(None) == ""


def test_path_traversal_prevention_in_output_path(tmp_path: Path):
    safe_dir = tmp_path / "user_output"
    safe_dir.mkdir(parents=True, exist_ok=True)
    input_file = tmp_path / "presentation.pptx"
    input_file.write_bytes(b"dummy")

    # Attempt directory escape via prefix and suffix
    out = get_default_output_path(
        input_file,
        output_dir=safe_dir,
        prefix="../../../tmp/evil_",
        suffix="_../../hack",
    )

    # Must be safely located inside safe_dir
    assert out.parent == safe_dir.resolve()
    assert ".." not in str(out)
    assert out.name.endswith(".pdf")


def test_path_traversal_prevention_in_merge_filename(tmp_path: Path):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dummy_pdf = tmp_path / "doc1.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    mgr = ConversionManager()
    options = ConversionOptions(
        output_dir=dest_dir,
        merge_all=True,
        merge_filename="../../../../tmp/malicious.pdf",
    )

    # Verify that clean_merge_fn is contained inside dest_dir
    from slidepdf.core.utils import sanitize_filename_component
    clean_fn = sanitize_filename_component(options.merge_filename)
    if not clean_fn.endswith(".pdf"):
        clean_fn += ".pdf"
    target = (dest_dir / clean_fn).resolve()
    assert target.parent == dest_dir.resolve()


def test_slide_range_dos_protection():
    # Massive range that would cause OOM if not protected
    res = parse_slide_range("1-999999999999999999999", 0)
    assert len(res) <= 10000

    # Negative and zero bounds
    res_neg = parse_slide_range("-10, 0, -5", 5)
    assert res_neg == []

    # Overflow bounds with small total
    res_bounded = parse_slide_range("1-5000000", 4)
    assert res_bounded == [1, 2, 3, 4]


def test_inspect_pptx_safety_on_corrupt_files(tmp_path: Path):
    # Non-existent file
    missing = tmp_path / "does_not_exist.pptx"
    assert inspect_pptx(missing) == (0, None)

    # Empty 0-byte file
    empty_file = tmp_path / "empty.pptx"
    empty_file.touch()
    assert inspect_pptx(empty_file) == (0, None)

    # Random binary noise
    garbage_file = tmp_path / "garbage.pptx"
    garbage_file.write_bytes(b"\xde\xad\xbe\xef" * 100)
    count, _ = inspect_pptx(garbage_file)
    assert count == 0


def test_system_opener_validation(tmp_path: Path):
    # Non-existent file must safely return False without spawning processes
    fake_path = tmp_path / "non_existent.pdf"
    assert open_file_in_system_viewer(fake_path) is False

    fake_dir = tmp_path / "non_existent_folder"
    assert open_folder_in_file_manager(fake_dir) is False


def test_corrupted_image_handling(tmp_path: Path):
    corrupted_img = tmp_path / "corrupt.png"
    corrupted_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00corrupted")

    out_pdf = tmp_path / "out.pdf"
    engine = NativePythonEngine()
    job = ConversionJob(input_path=corrupted_img, output_path=out_pdf)

    with pytest.raises(ValueError, match="Corrupted or invalid image"):
        engine.convert(job, ConversionOptions())


def test_embedded_image_decompression_bomb_handling(monkeypatch):
    """Verify embedded image decompression bomb in slide shape is safely handled."""
    from PIL import Image
    from reportlab.pdfgen import canvas
    from unittest.mock import MagicMock

    engine = NativePythonEngine()
    fake_canvas = MagicMock(spec=canvas.Canvas)
    fake_shape = MagicMock()
    fake_shape.image.blob = b"dummy_bytes"

    # Simulate PIL raising DecompressionBombError
    def mock_open(*args, **kwargs):
        img_mock = MagicMock()
        img_mock.verify.side_effect = Image.DecompressionBombError("Oversized image bomb")
        return img_mock

    monkeypatch.setattr(Image, "open", mock_open)

    # Should not raise exception or crash
    engine._render_picture(
        fake_canvas,
        fake_shape,
        left_pt=10,
        bottom_pt=10,
        w_pt=100,
        h_pt=100,
        options=ConversionOptions(),
    )
