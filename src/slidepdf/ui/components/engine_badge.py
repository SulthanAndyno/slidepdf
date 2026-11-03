"""Engine Status Badge and Diagnostic Dialog widget."""

from __future__ import annotations

import customtkinter as ctk
from slidepdf.core.engines.detector import EngineDetector
from slidepdf.core.models import EngineType
from slidepdf.ui import theme


class EngineBadge(ctk.CTkFrame):
    """Interactive badge indicating currently active/detected conversion engine."""

    def __init__(self, master, detector: EngineDetector, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.detector = detector

        self.btn = ctk.CTkButton(
            self,
            text="Checking engines...",
            font=theme.FONT_SMALL,
            corner_radius=12,
            height=26,
            command=self.show_diagnostics_modal,
        )
        self.btn.pack(side="right", padx=4, pady=2)
        self.update_badge_state()

    def update_badge_state(self, current_engine_type: EngineType = EngineType.AUTO) -> None:
        """Update badge text and color based on current selection or detection."""
        best = self.detector.get_engine(current_engine_type)
        if best.engine_type == EngineType.LIBREOFFICE:
            self.btn.configure(
                text="⚡ Engine: LibreOffice (Vector)",
                fg_color="#107c41",
                hover_color="#0b582e",
            )
        elif best.engine_type == EngineType.MSOFFICE:
            self.btn.configure(
                text="⚡ Engine: MS PowerPoint",
                fg_color="#d83b01",
                hover_color="#a82e01",
            )
        else:
            self.btn.configure(
                text="📦 Engine: Native Python",
                fg_color="#2b579a",
                hover_color="#1e3e6f",
            )

    def show_diagnostics_modal(self) -> None:
        """Open a modal window with full system engine diagnostics."""
        diag = self.detector.diagnose_system()

        top = ctk.CTkToplevel(self)
        top.title("Engine Diagnostics & Health Check")
        top.geometry("520x420")
        top.resizable(False, False)
        top.grab_set()

        # Header
        title = ctk.CTkLabel(
            top,
            text="Conversion Engines Diagnostics",
            font=theme.FONT_TITLE,
        )
        title.pack(padx=20, pady=(20, 10), anchor="w")

        info_box = ctk.CTkTextbox(top, font=theme.FONT_MONO, wrap="word", height=260)
        info_box.pack(padx=20, pady=10, fill="both", expand=True)

        report = (
            f"=== SlidePDF Studio System Diagnostics ===\n\n"
            f"Operating System: {diag['os']}\n"
            f"Python Runtime:   v{diag['python']}\n"
            f"Active Recommendation: {diag['best_engine']}\n\n"
            f"--- 1. Native Python Engine ---\n"
            f"Status:  {diag['native_status']}\n"
            f"Details: {diag['native_details']}\n\n"
            f"--- 2. LibreOffice Engine ---\n"
            f"Status:  {diag['libreoffice_status']}\n"
            f"Details: {diag['libreoffice_details']}\n\n"
            f"--- 3. Microsoft Office COM Engine ---\n"
            f"Status:  {diag['msoffice_status']}\n"
            f"Details: {diag['msoffice_details']}\n\n"
            f"Tip: LibreOffice provides the highest vector fidelity on Linux/macOS.\n"
            f"     If LibreOffice is not installed, Native Python Engine is used."
        )
        info_box.insert("1.0", report)
        info_box.configure(state="disabled")

        close_btn = ctk.CTkButton(
            top,
            text="Close",
            width=100,
            command=top.destroy,
        )
        close_btn.pack(pady=(0, 20))
