"""Tests for utility functions."""

from pathlib import Path
from slidepdf.core.utils import get_default_output_path, parse_slide_range


def test_parse_slide_range_all():
    assert parse_slide_range(None, 5) == [1, 2, 3, 4, 5]
    assert parse_slide_range("", 3) == [1, 2, 3]


def test_parse_slide_range_specific():
    assert parse_slide_range("1-3, 5", 10) == [1, 2, 3, 5]
    assert parse_slide_range("2, 4, 6", 8) == [2, 4, 6]
    assert parse_slide_range("4-2", 5) == []  # Invalid reversed range
    assert parse_slide_range("8-12", 10) == [8, 9, 10]  # Clamped to total_slides


def test_get_default_output_path():
    inp = Path("/home/user/presentation.pptx")
    out = get_default_output_path(inp)
    assert out == Path("/home/user/presentation.pdf")

    custom_out = get_default_output_path(inp, prefix="clean_", suffix="_final")
    assert custom_out == Path("/home/user/clean_presentation_final.pdf")

    dest_dir = Path("/tmp/output")
    out_in_dest = get_default_output_path(inp, output_dir=dest_dir)
    assert out_in_dest == Path("/tmp/output/presentation.pdf")
