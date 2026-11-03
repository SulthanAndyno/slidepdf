"""Main Application Window for SlidePDF Studio."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import List, Optional
import customtkinter as ctk

from slidepdf import __version__
from slidepdf.core.converter import ConversionManager
from slidepdf.core.engines.detector import EngineDetector
from slidepdf.core.models import (
    BatchResult,
    ConversionJob,
    ConversionOptions,
    EngineType,
    JobStatus,
)
from slidepdf.core.utils import ALL_SUPPORTED_EXTENSIONS
from slidepdf.ui import theme
from slidepdf.ui.components.engine_badge import EngineBadge
from slidepdf.ui.components.file_queue import FileQueueView
from slidepdf.ui.components.log_drawer import LogDrawer
from slidepdf.ui.components.settings_panel import SettingsPanel


class MainWindow(ctk.CTk):
    """Primary application window."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("SlidePDF Studio - PPTX to PDF Converter")
        self.geometry("1100x720")
        self.minsize(860, 580)

        # Core logic instances
        self.detector = EngineDetector()
        self.manager = ConversionManager(self.detector)
        self.is_converting = False

        # Load icon if available
        self._load_app_icon()

        # Build GUI
        self._build_ui()

        # Keyboard shortcuts
        self._bind_shortcuts()

        # Load files passed via arguments (e.g. Open With...)
        self._load_cli_files()

    def _load_cli_files(self) -> None:
        """Load presentations and documents passed via command line arguments into the queue."""
        initial_files = [
            Path(arg) for arg in sys.argv[1:]
            if Path(arg).is_file() and Path(arg).suffix.lower() in ALL_SUPPORTED_EXTENSIONS
        ]
        if initial_files:
            self.queue_view.add_files(initial_files)
            self.log_drawer.log(f"Pre-loaded {len(initial_files)} presentation(s) from arguments.")

    def _bind_shortcuts(self) -> None:
        """Bind global keyboard shortcuts for power users."""
        self.bind("<Control-o>", lambda e: self._on_add_files())
        self.bind("<Control-O>", lambda e: self._on_add_folder())
        self.bind("<Control-Shift-O>", lambda e: self._on_add_folder())
        self.bind("<Control-Return>", lambda e: self._start_conversion() if not self.is_converting else None)
        self.bind("<Control-KP_Enter>", lambda e: self._start_conversion() if not self.is_converting else None)
        self.bind("<Escape>", lambda e: self._on_cancel() if self.is_converting else None)
        self.bind("<Control-l>", lambda e: self.log_drawer.toggle())
        self.bind("<Control-d>", lambda e: self._on_clear_queue())
        self.bind("<Control-q>", lambda e: self.destroy())

    def _load_app_icon(self) -> None:
        """Attempt to set window icon from assets."""
        icon_path = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                # CustomTkinter supports iconbitmap on Windows, wm_iconphoto on Linux
                if sys.platform == "win32":
                    self.wm_iconbitmap(str(icon_path))
                else:
                    from PIL import ImageTk, Image
                    img = Image.open(str(icon_path))
                    self._tk_icon = ImageTk.PhotoImage(img)
                    self.wm_iconphoto(True, self._tk_icon)
            except Exception:
                pass

    def _build_ui(self) -> None:
        # 1. Top Header Bar
        self.header_frame = ctk.CTkFrame(self, height=54, corner_radius=0)
        self.header_frame.pack(fill="x", side="top")
        self._build_header()

        # 2. Main Content Split View (Left: Settings, Right: Work area)
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(fill="both", expand=True, padx=14, pady=(10, 14))

        # Left: Settings Sidebar
        self.settings_panel = SettingsPanel(
            self.main_content,
            width=290,
            on_engine_change=self._on_engine_change,
        )
        self.settings_panel.pack(side="left", fill="y", padx=(0, 12))

        # Right: Work area (Toolbar, Queue, Bottom Actions, Log Drawer)
        self.work_area = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.work_area.pack(side="right", fill="both", expand=True)
        self._build_work_area()

    def _build_header(self) -> None:
        self.header_frame.grid_columnconfigure(1, weight=1)

        # App branding
        brand_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_frame.pack(side="left", padx=16, pady=8)

        title_lbl = ctk.CTkLabel(
            brand_frame,
            text="SlidePDF Studio",
            font=theme.FONT_TITLE,
            text_color="#3B8ED0",
        )
        title_lbl.pack(side="left")

        ver_lbl = ctk.CTkLabel(
            brand_frame,
            text=f"v{__version__}",
            font=theme.FONT_SMALL,
            text_color="#888888",
        )
        ver_lbl.pack(side="left", padx=(6, 0), pady=(4, 0))

        # Theme mode toggle
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Dark Mode",
            font=theme.FONT_SMALL,
            command=self._toggle_theme,
        )
        self.theme_switch.select()  # default dark mode
        self.theme_switch.pack(side="right", padx=(8, 16), pady=12)

        # Engine Badge
        self.engine_badge = EngineBadge(self.header_frame, self.detector)
        self.engine_badge.pack(side="right", padx=8, pady=12)

    def _build_work_area(self) -> None:
        # Toolbar: Add Files, Add Folder, Clear All, Counter
        self.toolbar = ctk.CTkFrame(self.work_area, height=44, corner_radius=8)
        self.toolbar.pack(fill="x", pady=(0, 8))

        self.add_files_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Add Files (Ctrl+O)",
            font=theme.FONT_BODY_BOLD,
            width=135,
            command=self._on_add_files,
        )
        self.add_files_btn.pack(side="left", padx=(10, 6), pady=8)

        self.add_folder_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Add Folder (Ctrl+Shift+O)",
            font=theme.FONT_BODY,
            width=165,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self._on_add_folder,
        )
        self.add_folder_btn.pack(side="left", padx=6, pady=8)

        self.clear_btn = ctk.CTkButton(
            self.toolbar,
            text="Clear (Ctrl+D)",
            font=theme.FONT_SMALL,
            width=95,
            fg_color="transparent",
            text_color="#e74c3c",
            hover_color="#3a1b1b",
            command=self._on_clear_queue,
        )
        self.clear_btn.pack(side="left", padx=6, pady=8)

        self.queue_counter_lbl = ctk.CTkLabel(
            self.toolbar,
            text="0 files in queue",
            font=theme.FONT_SMALL,
            text_color="#888888",
        )
        self.queue_counter_lbl.pack(side="right", padx=16, pady=8)

        # File Queue View
        self.queue_view = FileQueueView(
            self.work_area,
            on_queue_change=self._on_queue_count_change,
        )
        self.queue_view.pack(fill="both", expand=True, pady=(0, 8))

        # Bottom Action Control Bar
        self.bottom_bar = ctk.CTkFrame(self.work_area, corner_radius=8)
        self.bottom_bar.pack(fill="x", pady=(0, 8))
        self._build_bottom_bar()

        # Log Drawer
        self.log_drawer = LogDrawer(self.work_area, default_open=False)
        self.log_drawer.pack(fill="x")

        # Initial log
        self.log_drawer.log(f"SlidePDF Studio v{__version__} initialized.")
        best_eng = self.detector.get_best_engine()
        self.log_drawer.log(f"System ready. Default engine: {best_eng.name}")

    def _build_bottom_bar(self) -> None:
        self.bottom_bar.grid_columnconfigure(0, weight=1)

        # Progress info
        info_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))

        self.status_lbl = ctk.CTkLabel(
            info_frame,
            text="Ready to convert",
            font=theme.FONT_BODY,
            anchor="w",
        )
        self.status_lbl.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.bottom_bar, height=10)
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Action Buttons frame (Right side)
        btn_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        btn_frame.grid(row=0, column=1, rowspan=2, padx=16, pady=10)

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=theme.FONT_BODY,
            width=85,
            height=36,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            state="disabled",
            command=self._on_cancel,
        )
        self.cancel_btn.pack(side="left", padx=(0, 8))

        self.convert_btn = ctk.CTkButton(
            btn_frame,
            text="Start Conversion (Ctrl+↵)",
            font=theme.FONT_BODY_BOLD,
            width=180,
            height=36,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._start_conversion,
        )
        self.convert_btn.pack(side="left")

    # ==================== User Action Handlers ====================

    def _toggle_theme(self) -> None:
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("Light")
            self.theme_switch.configure(text="Light Mode")

    def _on_engine_change(self, engine_type: EngineType) -> None:
        self.engine_badge.update_badge_state(engine_type)
        eng = self.detector.get_engine(engine_type)
        self.log_drawer.log(f"Active engine switched to: {eng.name}")

    def _on_add_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select Presentations, Images, or Documents",
            filetypes=[
                (
                    "All Supported Formats",
                    "*.pptx *.ppt *.pptm *.ppsx *.pps *.potx *.odp *.png *.jpg *.jpeg *.webp *.docx *.doc *.odt",
                ),
                ("PowerPoint & Presentations", "*.pptx *.ppt *.pptm *.ppsx *.pps *.potx *.odp"),
                ("Images to PDF", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff"),
                ("Documents", "*.docx *.doc *.odt *.rtf"),
                ("All files", "*.*"),
            ],
        )
        if files:
            paths = [Path(f) for f in files]
            count = self.queue_view.add_files(paths)
            self.log_drawer.log(f"Added {count} file(s) to conversion queue.")

    def _on_add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder containing Presentations or Images")
        if folder:
            f_path = Path(folder)
            files = [
                f for f in f_path.iterdir()
                if f.is_file() and f.suffix.lower() in ALL_SUPPORTED_EXTENSIONS
            ]
            if files:
                count = self.queue_view.add_files(files)
                self.log_drawer.log(f"Scanned folder '{f_path.name}': added {count} file(s).")
            else:
                messagebox.showinfo("No Files Found", f"No supported presentation or image files found in:\n{folder}")

    def _on_clear_queue(self) -> None:
        if not self.is_converting:
            self.queue_view.clear_all()
            self.progress_bar.set(0.0)
            self.status_lbl.configure(text="Queue cleared.")
            self.log_drawer.log("Queue cleared.")

    def _on_queue_count_change(self, count: int) -> None:
        self.queue_counter_lbl.configure(text=f"{count} file(s) in queue")
        if count == 0 and not self.is_converting:
            self.status_lbl.configure(text="Ready to convert")

    def _on_cancel(self) -> None:
        if self.is_converting:
            self.manager.cancel()
            self.status_lbl.configure(text="Cancelling conversion...")
            self.log_drawer.log("User initiated cancellation...", level="WARNING")
            self.cancel_btn.configure(state="disabled")

    # ==================== Conversion Workflow ====================

    def _start_conversion(self) -> None:
        jobs = self.queue_view.get_jobs()
        if not jobs:
            messagebox.showwarning("Empty Queue", "Please add at least one PowerPoint presentation to convert.")
            return

        options = self.settings_panel.get_conversion_options()

        self.is_converting = True
        self.convert_btn.configure(state="disabled", text="Converting...")
        self.cancel_btn.configure(state="normal")
        self.add_files_btn.configure(state="disabled")
        self.add_folder_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")

        self.progress_bar.set(0.0)
        self.status_lbl.configure(text="Starting conversion process...")
        self.log_drawer.log(f"Starting batch of {len(jobs)} files (Engine: {options.engine.value}).")

        # Launch background worker
        worker = threading.Thread(
            target=self._run_conversion_worker,
            args=(jobs, options),
            daemon=True,
        )
        worker.start()

    def _run_conversion_worker(self, jobs: List[ConversionJob], options: ConversionOptions) -> None:
        """Background thread executing conversion pipeline."""

        def _on_job_start(job: ConversionJob):
            self.after(0, lambda: self._ui_job_start(job))

        def _on_job_progress(job: ConversionJob, pct: float, msg: str):
            self.after(0, lambda: self._ui_job_progress(job, pct, msg))

        def _on_job_complete(job: ConversionJob):
            self.after(0, lambda: self._ui_job_complete(job))

        def _on_job_error(job: ConversionJob, exc: Exception):
            self.after(0, lambda: self._ui_job_error(job, exc))

        def _on_batch_progress(pct: float, msg: str):
            self.after(0, lambda: self._ui_batch_progress(pct, msg))

        batch_result = self.manager.convert_batch(
            jobs,
            options,
            on_job_start=_on_job_start,
            on_job_progress=_on_job_progress,
            on_job_complete=_on_job_complete,
            on_job_error=_on_job_error,
            on_batch_progress=_on_batch_progress,
        )

        self.after(0, lambda: self._ui_batch_finished(batch_result))

    # ==================== Thread-Safe UI Callbacks ====================

    def _ui_job_start(self, job: ConversionJob) -> None:
        self.queue_view.update_job_view(job)
        self.log_drawer.log(f"Starting conversion: {job.file_name}")

    def _ui_job_progress(self, job: ConversionJob, pct: float, msg: str) -> None:
        self.queue_view.update_job_view(job)

    def _ui_job_complete(self, job: ConversionJob) -> None:
        self.queue_view.update_job_view(job)
        self.log_drawer.log(
            f"✓ Finished: {job.file_name} -> {job.output_path.name if job.output_path else ''} "
            f"({job.elapsed_seconds:.2f}s)",
            level="SUCCESS",
        )

    def _ui_job_error(self, job: ConversionJob, exc: Exception) -> None:
        self.queue_view.update_job_view(job)
        self.log_drawer.log(f"✕ Failed {job.file_name}: {exc}", level="ERROR")

    def _ui_batch_progress(self, pct: float, msg: str) -> None:
        self.progress_bar.set(pct)
        self.status_lbl.configure(text=msg)

    def _ui_batch_finished(self, result: BatchResult) -> None:
        self.is_converting = False
        self.convert_btn.configure(state="normal", text="Start Conversion")
        self.cancel_btn.configure(state="disabled")
        self.add_files_btn.configure(state="normal")
        self.add_folder_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.progress_bar.set(1.0)

        summary_msg = (
            f"Batch completed in {result.total_elapsed_seconds:.2f}s: "
            f"{result.completed_jobs} succeeded, {result.failed_jobs} failed."
        )
        self.status_lbl.configure(text=summary_msg)
        self.log_drawer.log(summary_msg, level="SUCCESS" if result.is_success else "WARNING")

        if result.merged_pdf_path:
            self.log_drawer.log(f"Merged PDF created at: {result.merged_pdf_path}", level="SUCCESS")

        # Completion dialog
        if result.completed_jobs > 0:
            merge_note = f"\n\nMerged PDF:\n{result.merged_pdf_path}" if result.merged_pdf_path else ""
            messagebox.showinfo(
                "Conversion Finished",
                f"Successfully converted {result.completed_jobs} presentation(s)!{merge_note}",
            )
