"""Command Line Interface for SlidePDF Studio."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from slidepdf import __version__
from slidepdf.core.converter import ConversionManager
from slidepdf.core.engines.detector import EngineDetector
from slidepdf.core.models import (
    ConversionJob,
    ConversionOptions,
    EngineType,
    JobStatus,
    PDFQuality,
)
from slidepdf.core.utils import ALL_SUPPORTED_EXTENSIONS, inspect_pptx

console = Console()


def print_banner() -> None:
    """Print the application banner."""
    title = f"[bold cyan]SlidePDF Studio[/bold cyan] [dim]v{__version__}[/dim]"
    subtitle = "[dim]Professional PPTX to PDF Conversion Suite[/dim]"
    console.print(Panel(f"{title}\n{subtitle}", expand=False, border_style="cyan"))


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run system diagnostics for conversion engines."""
    print_banner()
    console.print("\n[bold]Running System Health & Engine Diagnostics...[/bold]\n")

    detector = EngineDetector()
    diag = detector.diagnose_system()

    table = Table(title="System Environment & Available Engines", border_style="blue")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status / Detection", style="magenta")
    table.add_column("Details", style="green")

    table.add_row("Operating System", "Detected", diag["os"])
    table.add_row("Python Version", "Detected", diag["python"])
    table.add_row("Best Engine (Auto)", "Recommended", diag["best_engine"])

    table.add_section()
    table.add_row("Native Python Engine", diag["native_status"], diag["native_details"])
    table.add_row("LibreOffice Engine", diag["libreoffice_status"], diag["libreoffice_details"])
    table.add_row("MS Office COM Engine", diag["msoffice_status"], diag["msoffice_details"])

    console.print(table)

    # Recommendations
    if diag["libreoffice_status"] != "Available" and "Windows" not in diag["os"]:
        console.print(
            "\n[yellow]Tip:[/yellow] For 100% complex OpenXML rendering fidelity on Linux/macOS, "
            "installing LibreOffice is recommended:\n"
            "  • Arch Linux:   [bold]sudo pacman -S libreoffice-fresh[/bold]\n"
            "  • Ubuntu/Debian: [bold]sudo apt install libreoffice[/bold]\n"
            "  • macOS:        [bold]brew install --cask libreoffice[/bold]\n"
            "SlidePDF Studio will seamlessly use the built-in [bold green]Native Python Engine[/bold green] "
            "as a zero-dependency fallback."
        )

    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    """Convert a single presentation file."""
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Input file does not exist: {input_path}")
        return 1

    print_banner()
    console.print(f"\n[cyan]Input file:[/cyan] {input_path}")

    # Inspect presentation
    slide_count, title = inspect_pptx(input_path)
    title_str = f" ('{title}')" if title else ""
    console.print(f"[dim]Slides detected: {slide_count}{title_str}[/dim]")

    engine_type = EngineType.from_string(args.engine)
    quality = PDFQuality.COMPRESSED if args.compress else PDFQuality.STANDARD

    options = ConversionOptions(
        output_dir=Path(args.output).parent if args.output else None,
        engine=engine_type,
        quality=quality,
        slide_range=args.slides,
        prefix=args.prefix or "",
        suffix=args.suffix or "",
        open_after_conversion=args.open,
        watermark_text=args.watermark,
        watermark_opacity=args.watermark_opacity,
        password=args.password,
        handout_mode=args.handout,
        page_numbers=args.page_numbers,
        page_number_format=args.page_number_format,
    )

    out_file = Path(args.output) if args.output else None
    job = ConversionJob(input_path=input_path, output_path=out_file)

    mgr = ConversionManager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Converting {input_path.name}...", total=100)

        def _on_prog(pct: float, msg: str):
            progress.update(task, completed=int(pct * 100), description=msg)

        try:
            result_path = mgr.convert_single(job, options, on_progress=_on_prog)
            progress.update(task, completed=100, description="[bold green]Completed![/bold green]")
        except Exception as exc:
            console.print(f"\n[bold red]Conversion Failed:[/bold red] {exc}")
            return 1

    console.print(
        f"\n[bold green]✓ Conversion successful![/bold green]\n"
        f"  Output PDF: [cyan]{result_path}[/cyan]\n"
        f"  File size:  [dim]{job.formatted_size}[/dim]\n"
        f"  Time taken: [dim]{job.elapsed_seconds:.2f}s[/dim]"
    )
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Batch convert presentations in a folder or multiple files."""
    print_banner()

    input_targets = [Path(p) for p in args.targets]
    found_files: List[Path] = []

    for target in input_targets:
        if target.is_dir():
            pattern = "**/*" if args.recursive else "*"
            for f in target.glob(pattern):
                if f.is_file() and f.suffix.lower() in ALL_SUPPORTED_EXTENSIONS:
                    found_files.append(f)
        elif target.is_file() and target.suffix.lower() in ALL_SUPPORTED_EXTENSIONS:
            found_files.append(target)

    # Deduplicate and sort
    found_files = sorted(list(set(found_files)))

    if not found_files:
        console.print("[bold yellow]No supported presentation, document, or image files found.[/bold yellow]")
        return 1

    console.print(f"\n[bold]Found {len(found_files)} file(s) for batch conversion:[/bold]")
    for idx, f in enumerate(found_files[:10], start=1):
        console.print(f"  {idx}. [cyan]{f.name}[/cyan] ({f.stat().st_size / 1024:.1f} KB)")
    if len(found_files) > 10:
        console.print(f"  [dim]... and {len(found_files) - 10} more files[/dim]")

    engine_type = EngineType.from_string(args.engine)
    quality = PDFQuality.COMPRESSED if args.compress else PDFQuality.STANDARD
    out_dir = Path(args.output) if args.output else None

    options = ConversionOptions(
        output_dir=out_dir,
        engine=engine_type,
        quality=quality,
        slide_range=args.slides,
        merge_all=args.merge,
        merge_filename=args.merge_name or "merged_presentations.pdf",
        prefix=args.prefix or "",
        suffix=args.suffix or "",
        open_after_conversion=args.open,
        watermark_text=args.watermark,
        watermark_opacity=args.watermark_opacity,
        password=args.password,
        handout_mode=args.handout,
        page_numbers=args.page_numbers,
        page_number_format=args.page_number_format,
    )

    jobs = [ConversionJob(input_path=p) for p in found_files]
    mgr = ConversionManager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        batch_task = progress.add_task("Batch Processing...", total=100)

        def _on_batch_prog(pct: float, msg: str):
            progress.update(batch_task, completed=int(pct * 100), description=msg)

        batch_result = mgr.convert_batch(jobs, options, on_batch_progress=_on_batch_prog)

    # Result Summary Table
    table = Table(title="Batch Conversion Summary", border_style="cyan")
    table.add_column("File Name", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Time", justify="right")
    table.add_column("Details", style="dim")

    for job in batch_result.jobs:
        status_color = "green" if job.status == JobStatus.COMPLETED else "red"
        status_text = f"[{status_color}]{job.status.value.upper()}[/{status_color}]"
        detail = str(job.output_path.name) if job.output_path else (job.error_message or "")
        table.add_row(job.file_name, status_text, f"{job.elapsed_seconds:.2f}s", detail)

    console.print(table)

    if batch_result.merged_pdf_path:
        console.print(
            f"\n[bold green]Merged PDF created:[/bold green] [cyan]{batch_result.merged_pdf_path}[/cyan]"
        )

    console.print(
        f"\n[bold]Done:[/bold] {batch_result.completed_jobs} succeeded, "
        f"{batch_result.failed_jobs} failed. Total time: {batch_result.total_elapsed_seconds:.2f}s"
    )

    return 0 if batch_result.failed_jobs == 0 else 1


def cmd_gui(args: argparse.Namespace) -> int:
    """Launch desktop GUI application."""
    try:
        from slidepdf.app import main as gui_main
        gui_main()
        return 0
    except Exception as exc:
        console.print(f"[bold red]Failed to start GUI:[/bold red] {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="slidepdf",
        description="SlidePDF Studio - Professional PPTX to PDF Converter",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: convert
    p_convert = subparsers.add_parser("convert", help="Convert a single PPTX presentation")
    p_convert.add_argument("input", help="Path to input .pptx or .ppt file")
    p_convert.add_argument("-o", "--output", help="Destination PDF path")
    p_convert.add_argument(
        "-e",
        "--engine",
        choices=["auto", "libreoffice", "msoffice", "native"],
        default="auto",
        help="Conversion engine (default: auto)",
    )
    p_convert.add_argument("-s", "--slides", help="Slide range (e.g., '1-5, 8, 10-12')")
    p_convert.add_argument("--compress", action="store_true", help="Optimize & compress output PDF")
    p_convert.add_argument("--prefix", default="", help="Prefix added to output filename")
    p_convert.add_argument("--suffix", default="", help="Suffix added to output filename")
    p_convert.add_argument("--open", action="store_true", help="Open PDF in default viewer when finished")
    p_convert.add_argument("--watermark", help="Transparent text watermark to stamp on slides")
    p_convert.add_argument("--watermark-opacity", type=float, default=0.2, help="Watermark opacity (0.05 to 1.0, default: 0.2)")
    p_convert.add_argument("--password", help="Encrypt and password-protect the output PDF")
    p_convert.add_argument(
        "--handout",
        type=int,
        choices=[1, 2, 4],
        default=1,
        help="Handout layout (1: standard 1-up, 2: 2 slides/page, 4: 4 slides/page)",
    )
    p_convert.add_argument("--page-numbers", action="store_true", help="Add page/slide numbering (Page X of Y)")
    p_convert.add_argument("--page-number-format", default="Page {n} of {total}", help="Page number format string")
    p_convert.set_defaults(func=cmd_convert)

    # Command: batch
    p_batch = subparsers.add_parser("batch", help="Batch convert multiple presentations or folders")
    p_batch.add_argument("targets", nargs="+", help="Folders or files to convert")
    p_batch.add_argument("-o", "--output", help="Destination directory")
    p_batch.add_argument(
        "-e",
        "--engine",
        choices=["auto", "libreoffice", "msoffice", "native"],
        default="auto",
        help="Conversion engine (default: auto)",
    )
    p_batch.add_argument("-r", "--recursive", action="store_true", help="Scan subdirectories recursively")
    p_batch.add_argument("-m", "--merge", action="store_true", help="Merge all converted PDFs into one file")
    p_batch.add_argument("--merge-name", default="merged_presentations.pdf", help="Merged PDF filename")
    p_batch.add_argument("-s", "--slides", help="Slide range applied to all files")
    p_batch.add_argument("--compress", action="store_true", help="Compress images in output PDF")
    p_batch.add_argument("--prefix", default="", help="Prefix for output filenames")
    p_batch.add_argument("--suffix", default="", help="Suffix for output filenames")
    p_batch.add_argument("--open", action="store_true", help="Open merged PDF when complete")
    p_batch.add_argument("--watermark", help="Transparent text watermark to stamp across slides")
    p_batch.add_argument("--watermark-opacity", type=float, default=0.2, help="Watermark opacity (0.05 to 1.0, default: 0.2)")
    p_batch.add_argument("--password", help="Encrypt and password-protect the output PDF")
    p_batch.add_argument(
        "--handout",
        type=int,
        choices=[1, 2, 4],
        default=1,
        help="Handout layout (1: standard 1-up, 2: 2 slides/page, 4: 4 slides/page)",
    )
    p_batch.add_argument("--page-numbers", action="store_true", help="Add page/slide numbering (Page X of Y)")
    p_batch.add_argument("--page-number-format", default="Page {n} of {total}", help="Page number format string")
    p_batch.set_defaults(func=cmd_batch)

    # Command: doctor
    p_doctor = subparsers.add_parser("doctor", help="Check system health and engine availability")
    p_doctor.set_defaults(func=cmd_doctor)

    # Command: gui
    p_gui = subparsers.add_parser("gui", help="Launch the Desktop GUI application")
    p_gui.set_defaults(func=cmd_gui)

    return parser


def main() -> None:
    """Entrypoint for the CLI."""
    parser = build_parser()
    if len(sys.argv) == 1:
        # If no arguments provided, default to launching GUI
        sys.exit(cmd_gui(argparse.Namespace()))

    args = parser.parse_args()
    if hasattr(args, "func"):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
