"""File Queue and task list widget."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from slidepdf.core.models import ConversionJob, JobStatus
from slidepdf.core.utils import ALL_SUPPORTED_EXTENSIONS, inspect_pptx, open_file_in_system_viewer
from slidepdf.ui import theme


class QueueItemRow(ctk.CTkFrame):
    """An individual file item row in the queue list."""

    def __init__(
        self,
        master,
        job: ConversionJob,
        on_remove: Callable[[str], None],
        on_move_up: Optional[Callable[[str], None]] = None,
        on_move_down: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, height=48, **kwargs)
        self.job = job
        self.on_remove = on_remove
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        # 1. Icon badge based on file extension
        ext = self.job.input_path.suffix.lower()
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
            badge_text = "IMG"
            badge_color = "#8e44ad"
        elif ext == ".odp":
            badge_text = "ODP"
            badge_color = "#27ae60"
        elif ext in (".docx", ".doc", ".odt"):
            badge_text = "DOC"
            badge_color = "#2980b9"
        elif ext == ".pdf":
            badge_text = "PDF"
            badge_color = "#c0392b"
        else:
            badge_text = "PPT" if ext == ".ppt" else "PPTX"
            badge_color = "#d35400"

        self.icon_badge = ctk.CTkLabel(
            self,
            text=badge_text,
            font=theme.FONT_SMALL,
            fg_color=badge_color,
            text_color="#ffffff",
            corner_radius=4,
            width=38,
            height=22,
        )
        self.icon_badge.grid(row=0, column=0, padx=(10, 8), pady=8)

        # 2. File info (Name + details)
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w", padx=2, pady=4)

        self.name_lbl = ctk.CTkLabel(
            info_frame,
            text=self.job.file_name,
            font=theme.FONT_BODY_BOLD,
            anchor="w",
        )
        self.name_lbl.pack(anchor="w")

        slides_text = f"{self.job.total_slides} slides" if self.job.total_slides > 0 else "slides pending"
        self.meta_lbl = ctk.CTkLabel(
            info_frame,
            text=f"{slides_text} • {self.job.formatted_size}",
            font=theme.FONT_SMALL,
            text_color="#888888",
            anchor="w",
        )
        self.meta_lbl.pack(anchor="w")

        # 3. Mini Progress Bar
        self.prog_bar = ctk.CTkProgressBar(self, width=100, height=8)
        self.prog_bar.set(0.0)
        self.prog_bar.grid(row=0, column=2, padx=10, pady=8)
        self.prog_bar.grid_remove()  # hidden initially

        # 4. Status Badge
        self.status_badge = ctk.CTkLabel(
            self,
            text="QUEUED",
            font=theme.FONT_SMALL,
            corner_radius=6,
            fg_color="#495057",
            text_color="#ffffff",
            width=75,
            height=22,
        )
        self.status_badge.grid(row=0, column=3, padx=8, pady=8)

        # 5. Actions: Open PDF button
        self.open_btn = ctk.CTkButton(
            self,
            text="Open PDF",
            width=70,
            height=24,
            font=theme.FONT_SMALL,
            fg_color=theme.COLOR_PRIMARY,
            command=self._open_result,
        )
        self.open_btn.grid(row=0, column=4, padx=4, pady=8)
        self.open_btn.grid_remove()  # only show when completed

        # 6. Reorder buttons (Move Up / Move Down)
        self.move_up_btn = ctk.CTkButton(
            self,
            text="▲",
            width=22,
            height=24,
            font=theme.FONT_SMALL,
            fg_color="transparent",
            hover_color="#334455",
            text_color="#888888",
            command=lambda: self.on_move_up(self.job.job_id) if self.on_move_up else None,
        )
        self.move_up_btn.grid(row=0, column=5, padx=1, pady=8)

        self.move_down_btn = ctk.CTkButton(
            self,
            text="▼",
            width=22,
            height=24,
            font=theme.FONT_SMALL,
            fg_color="transparent",
            hover_color="#334455",
            text_color="#888888",
            command=lambda: self.on_move_down(self.job.job_id) if self.on_move_down else None,
        )
        self.move_down_btn.grid(row=0, column=6, padx=1, pady=8)

        # 7. Remove button
        self.remove_btn = ctk.CTkButton(
            self,
            text="✕",
            width=24,
            height=24,
            font=theme.FONT_SMALL,
            fg_color="transparent",
            hover_color="#552222",
            text_color="#aaaaaa",
            command=lambda: self.on_remove(self.job.job_id),
        )
        self.remove_btn.grid(row=0, column=7, padx=(2, 10), pady=8)

    def _open_result(self) -> None:
        if self.job.output_path and self.job.output_path.exists():
            open_file_in_system_viewer(self.job.output_path)

    def update_view(self) -> None:
        """Update row visual components based on current job state."""
        # Meta label update
        slides_text = f"{self.job.total_slides} slides" if self.job.total_slides > 0 else "slides"
        self.meta_lbl.configure(text=f"{slides_text} • {self.job.formatted_size}")

        # Status & progress
        st = self.job.status
        if st == JobStatus.PENDING:
            self.status_badge.configure(text="QUEUED", fg_color="#495057")
            self.prog_bar.grid_remove()
            self.open_btn.grid_remove()
        elif st == JobStatus.PROCESSING:
            self.status_badge.configure(text="CONVERTING", fg_color="#0056b3")
            self.prog_bar.grid()
            self.prog_bar.set(self.job.progress)
        elif st == JobStatus.COMPLETED:
            self.status_badge.configure(text="DONE ✓", fg_color="#1e7e34")
            self.prog_bar.grid_remove()
            self.open_btn.grid()
        elif st == JobStatus.FAILED:
            self.status_badge.configure(text="FAILED ✕", fg_color="#bd2130")
            self.prog_bar.grid_remove()
            self.open_btn.grid_remove()
        elif st == JobStatus.CANCELLED:
            self.status_badge.configure(text="CANCELLED", fg_color="#d39e00")
            self.prog_bar.grid_remove()


class FileQueueView(ctk.CTkFrame):
    """Container holding the scrollable list of jobs."""

    def __init__(self, master, on_queue_change: Optional[Callable[[int], None]] = None, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.on_queue_change = on_queue_change
        self.jobs: List[ConversionJob] = []
        self._item_rows: Dict[str, QueueItemRow] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        # Empty placeholder state
        self.empty_label = ctk.CTkLabel(
            self,
            text="No presentations added yet.\n\nClick '+ Add Files' or '+ Add Folder' above\nto begin your conversion queue.",
            font=theme.FONT_BODY,
            text_color="#777777",
            justify="center",
        )
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

        # Scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.scroll_frame.pack_forget()

    def add_files(self, paths: List[Path]) -> int:
        """Add new PowerPoint presentations to the queue."""
        added_count = 0
        existing_paths = {j.input_path.resolve() for j in self.jobs}

        for p in paths:
            p_res = p.resolve()
            if p_res in existing_paths:
                continue
            if p.suffix.lower() not in ALL_SUPPORTED_EXTENSIONS:
                continue

            # Inspect slide count in background or fast check
            slides, _ = inspect_pptx(p)
            job = ConversionJob(input_path=p, total_slides=slides)
            self.jobs.append(job)
            existing_paths.add(p_res)

            # Create visual row
            row = QueueItemRow(
                self.scroll_frame,
                job,
                on_remove=self.remove_job,
                on_move_up=self.move_job_up,
                on_move_down=self.move_job_down,
            )
            row.pack(fill="x", padx=4, pady=3)
            self._item_rows[job.job_id] = row
            added_count += 1

        self._update_display_mode()
        if self.on_queue_change:
            self.on_queue_change(len(self.jobs))
        return added_count

    def move_job_up(self, job_id: str) -> None:
        """Move a job one position earlier in queue."""
        idx = next((i for i, j in enumerate(self.jobs) if j.job_id == job_id), -1)
        if idx > 0:
            self.jobs[idx - 1], self.jobs[idx] = self.jobs[idx], self.jobs[idx - 1]
            self._repack_rows()

    def move_job_down(self, job_id: str) -> None:
        """Move a job one position later in queue."""
        idx = next((i for i, j in enumerate(self.jobs) if j.job_id == job_id), -1)
        if 0 <= idx < len(self.jobs) - 1:
            self.jobs[idx], self.jobs[idx + 1] = self.jobs[idx + 1], self.jobs[idx]
            self._repack_rows()

    def _repack_rows(self) -> None:
        """Re-pack row widgets in the current self.jobs order."""
        for job in self.jobs:
            row = self._item_rows.get(job.job_id)
            if row:
                row.pack_forget()
                row.pack(fill="x", padx=4, pady=3)

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the queue."""
        if job_id in self._item_rows:
            row = self._item_rows.pop(job_id)
            row.destroy()

        self.jobs = [j for j in self.jobs if j.job_id != job_id]
        self._update_display_mode()
        if self.on_queue_change:
            self.on_queue_change(len(self.jobs))

    def clear_all(self) -> None:
        """Clear the entire file queue."""
        for row in self._item_rows.values():
            row.destroy()
        self._item_rows.clear()
        self.jobs.clear()
        self._update_display_mode()
        if self.on_queue_change:
            self.on_queue_change(0)

    def _update_display_mode(self) -> None:
        if self.jobs:
            self.empty_label.place_forget()
            self.scroll_frame.pack(fill="both", expand=True, padx=6, pady=6)
        else:
            self.scroll_frame.pack_forget()
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def update_job_view(self, job: ConversionJob) -> None:
        """Trigger UI refresh for a specific job."""
        if job.job_id in self._item_rows:
            self._item_rows[job.job_id].update_view()

    def get_jobs(self) -> List[ConversionJob]:
        return list(self.jobs)
