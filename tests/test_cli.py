"""Tests for CLI parsing and commands."""

from slidepdf.cli import build_parser, cmd_doctor
import argparse


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["doctor"])
    assert args.command == "doctor"

    args_conv = parser.parse_args(["convert", "test.pptx", "-o", "out.pdf", "--engine", "native"])
    assert args_conv.command == "convert"
    assert args_conv.input == "test.pptx"
    assert args_conv.output == "out.pdf"
    assert args_conv.engine == "native"

    args_batch = parser.parse_args(["batch", "folder1", "--merge", "--recursive"])
    assert args_batch.command == "batch"
    assert args_batch.targets == ["folder1"]
    assert args_batch.merge is True
    assert args_batch.recursive is True


def test_cli_doctor_execution():
    args = argparse.Namespace()
    ret = cmd_doctor(args)
    assert ret == 0
