"""High-level Conversion Coordinator and Pipeline Manager."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional

from slidepdf.core.engines.detector import EngineDetector
from slidepdf.core.merger import PDFMergerUtil
from slidepdf.core.models import (
    BatchResult,
    ConversionJob,
    ConversionOptions,
    EngineType,
    JobStatus,
)
from slidepdf.core.utils import (
    get_default_output_path,
    open_file_in_system_viewer,
    open_folder_in_file_manager,
    sanitize_filename_component,
)


class ConversionManager:
    """Coordinates conversions across individual and batch presentation jobs."""

    def __init__(self, detector: Optional[EngineDetector] = None):
        self.detector = detector or EngineDetector()
        self._is_cancelled = False

    def cancel(self) -> None:
        """Signal the manager to cancel the active conversion pipeline."""
        self._is_cancelled = True

    def reset_cancellation(self) -> None:
        """Reset the cancellation flag."""
        self._is_cancelled = False

    def convert_single(
        self,
        job: ConversionJob,
        options: ConversionOptions,
        on_progress: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        """Execute conversion for a single presentation job."""
        self._is_cancelled = False
        start_time = time.time()
        job.status = JobStatus.PROCESSING
        job.progress = 0.0
        job.error_message = None

        try:
            # Resolve engine
            engine = self.detector.get_engine(options.engine)
            job.engine_used = engine.engine_type

            def _progress_wrapper(pct: float, msg: str) -> None:
                job.progress = pct
                if on_progress:
                    on_progress(pct, msg)

            output_file = engine.convert(job, options, progress_callback=_progress_wrapper)

            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.output_path = output_file
            job.elapsed_seconds = time.time() - start_time

            # Optional post actions
            if options.open_after_conversion and output_file.exists():
                open_file_in_system_viewer(output_file)
            elif options.open_folder_after and output_file.exists():
                open_folder_in_file_manager(output_file.parent)

            return output_file

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.elapsed_seconds = time.time() - start_time
            raise

    def convert_batch(
        self,
        jobs: List[ConversionJob],
        options: ConversionOptions,
        on_job_start: Optional[Callable[[ConversionJob], None]] = None,
        on_job_progress: Optional[Callable[[ConversionJob, float, str], None]] = None,
        on_job_complete: Optional[Callable[[ConversionJob], None]] = None,
        on_job_error: Optional[Callable[[ConversionJob, Exception], None]] = None,
        on_batch_progress: Optional[Callable[[float, str], None]] = None,
    ) -> BatchResult:
        """Execute batch conversion across multiple jobs with optional merging."""
        self.reset_cancellation()
        batch_start_time = time.time()
        batch_result = BatchResult(total_jobs=len(jobs), jobs=jobs)
        generated_pdfs: List[Path] = []

        total = len(jobs)
        for idx, job in enumerate(jobs, start=1):
            if self._is_cancelled:
                job.status = JobStatus.CANCELLED
                batch_result.cancelled_jobs += 1
                continue

            if on_job_start:
                on_job_start(job)

            if on_batch_progress:
                batch_pct = (idx - 1) / total
                on_batch_progress(batch_pct, f"Processing file {idx} of {total}: {job.file_name}")

            def _job_progress_cb(pct: float, msg: str) -> None:
                job.progress = pct
                if on_job_progress:
                    on_job_progress(job, pct, msg)

            try:
                out_path = self.convert_single(job, options, on_progress=_job_progress_cb)
                generated_pdfs.append(out_path)
                batch_result.completed_jobs += 1
                if on_job_complete:
                    on_job_complete(job)
            except Exception as exc:
                batch_result.failed_jobs += 1
                if on_job_error:
                    on_job_error(job, exc)

        # Merge operation if requested
        if options.merge_all and generated_pdfs and not self._is_cancelled:
            if on_batch_progress:
                on_batch_progress(0.92, "Merging all converted presentations into a single PDF...")

            dest_dir = (options.output_dir or (jobs[0].input_path.parent if jobs else Path.cwd())).resolve()
            clean_merge_fn = sanitize_filename_component(options.merge_filename) or "merged_presentation.pdf"
            if not clean_merge_fn.lower().endswith(".pdf"):
                clean_merge_fn += ".pdf"
            merge_target = dest_dir / clean_merge_fn

            merged_path = PDFMergerUtil.merge_pdfs(
                pdf_paths=generated_pdfs,
                output_path=merge_target,
                add_bookmarks=True,
                title="Consolidated Presentation Document",
            )
            batch_result.merged_pdf_path = merged_path

            if options.open_after_conversion and merged_path.exists():
                open_file_in_system_viewer(merged_path)

        batch_result.total_elapsed_seconds = time.time() - batch_start_time

        if on_batch_progress:
            on_batch_progress(
                1.0,
                f"Batch finished: {batch_result.completed_jobs} succeeded, {batch_result.failed_jobs} failed.",
            )

        return batch_result
