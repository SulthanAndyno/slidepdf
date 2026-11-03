"""Settings sidebar panel widget."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk
from tkinter import filedialog

from slidepdf.core.models import ConversionOptions, EngineType, PDFQuality
from slidepdf.ui import theme


class SettingsPanel(ctk.CTkFrame):
    """Configuration sidebar panel."""

    def __init__(self, master, on_engine_change: Optional[Callable[[EngineType], None]] = None, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.on_engine_change = on_engine_change

        self._build_ui()

    def _build_ui(self) -> None:
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Conversion Settings",
            font=theme.FONT_SUBTITLE,
            anchor="w",
        )
        title_label.pack(fill="x", padx=16, pady=(16, 12))

        # 1. Mode Selection (Individual vs Merge)
        mode_label = ctk.CTkLabel(self, text="Processing Mode:", font=theme.FONT_BODY_BOLD, anchor="w")
        mode_label.pack(fill="x", padx=16, pady=(4, 2))

        self.mode_var = ctk.StringVar(value="individual")
        self.mode_seg = ctk.CTkSegmentedButton(
            self,
            values=["Individual", "Merge All"],
            variable=self.mode_var,
            command=self._on_mode_change,
        )
        self.mode_seg.pack(fill="x", padx=16, pady=(0, 10))

        # Merged filename frame (hidden by default)
        self.merge_frame = ctk.CTkFrame(self, fg_color="transparent")
        merge_fn_label = ctk.CTkLabel(self.merge_frame, text="Merged Filename:", font=theme.FONT_SMALL, anchor="w")
        merge_fn_label.pack(fill="x")
        self.merge_filename_entry = ctk.CTkEntry(self.merge_frame, placeholder_text="merged_all.pdf")
        self.merge_filename_entry.insert(0, "merged_presentation.pdf")
        self.merge_filename_entry.pack(fill="x", pady=(2, 6))

        # 2. Engine Selection
        engine_label = ctk.CTkLabel(self, text="Conversion Engine:", font=theme.FONT_BODY_BOLD, anchor="w")
        engine_label.pack(fill="x", padx=16, pady=(6, 2))

        self.engine_var = ctk.StringVar(value="Auto-detect (Recommended)")
        self.engine_menu = ctk.CTkOptionMenu(
            self,
            variable=self.engine_var,
            values=[
                "Auto-detect (Recommended)",
                "Native Python Engine",
                "LibreOffice Engine",
                "Microsoft Office Engine",
            ],
            command=self._on_engine_selected,
        )
        self.engine_menu.pack(fill="x", padx=16, pady=(0, 10))

        # 3. Destination Directory
        dest_label = ctk.CTkLabel(self, text="Output Directory:", font=theme.FONT_BODY_BOLD, anchor="w")
        dest_label.pack(fill="x", padx=16, pady=(6, 2))

        self.same_folder_var = ctk.BooleanVar(value=True)
        self.same_folder_check = ctk.CTkCheckBox(
            self,
            text="Same as input file",
            variable=self.same_folder_var,
            command=self._toggle_output_dir,
            font=theme.FONT_BODY,
        )
        self.same_folder_check.pack(fill="x", padx=16, pady=(2, 6))

        self.custom_dest_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dest_path_entry = ctk.CTkEntry(
            self.custom_dest_frame,
            placeholder_text="Choose folder...",
            font=theme.FONT_SMALL,
        )
        self.dest_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.browse_dest_btn = ctk.CTkButton(
            self.custom_dest_frame,
            text="Browse",
            width=65,
            command=self._browse_custom_dest,
        )
        self.browse_dest_btn.pack(side="right")

        # 4. Slide Range
        range_label = ctk.CTkLabel(self, text="Slide Range (Optional):", font=theme.FONT_BODY_BOLD, anchor="w")
        range_label.pack(fill="x", padx=16, pady=(10, 2))
        self.slide_range_entry = ctk.CTkEntry(
            self,
            placeholder_text="All (or e.g. 1-3, 5)",
            font=theme.FONT_BODY,
        )
        self.slide_range_entry.pack(fill="x", padx=16, pady=(0, 10))

        # 5. Quality
        quality_label = ctk.CTkLabel(self, text="PDF Quality:", font=theme.FONT_BODY_BOLD, anchor="w")
        quality_label.pack(fill="x", padx=16, pady=(6, 2))
        self.quality_var = ctk.StringVar(value="Standard (Vector)")
        self.quality_seg = ctk.CTkSegmentedButton(
            self,
            values=["Standard (Vector)", "Compressed"],
            variable=self.quality_var,
        )
        self.quality_seg.pack(fill="x", padx=16, pady=(0, 10))

        # 6. Post-Conversion Options
        post_label = ctk.CTkLabel(self, text="Post Actions:", font=theme.FONT_BODY_BOLD, anchor="w")
        post_label.pack(fill="x", padx=16, pady=(6, 2))

        self.open_pdf_var = ctk.BooleanVar(value=False)
        self.open_pdf_check = ctk.CTkCheckBox(
            self,
            text="Open PDF when done",
            variable=self.open_pdf_var,
            font=theme.FONT_BODY,
        )
        self.open_pdf_check.pack(fill="x", padx=16, pady=2)

        self.open_folder_var = ctk.BooleanVar(value=False)
        self.open_folder_check = ctk.CTkCheckBox(
            self,
            text="Open folder when done",
            variable=self.open_folder_var,
            font=theme.FONT_BODY,
        )
        self.open_folder_check.pack(fill="x", padx=16, pady=2)

    def _on_mode_change(self, value: str) -> None:
        if value == "Merge All":
            self.merge_frame.pack(fill="x", padx=16, pady=(0, 10), after=self.mode_seg)
        else:
            self.merge_frame.pack_forget()

    def _toggle_output_dir(self) -> None:
        if self.same_folder_var.get():
            self.custom_dest_frame.pack_forget()
        else:
            self.custom_dest_frame.pack(fill="x", padx=16, pady=(0, 10), after=self.same_folder_check)

    def _browse_custom_dest(self) -> None:
        chosen = filedialog.askdirectory(title="Select Output Folder")
        if chosen:
            self.dest_path_entry.delete(0, "end")
            self.dest_path_entry.insert(0, chosen)

    def _on_engine_selected(self, choice: str) -> None:
        if self.on_engine_change:
            self.on_engine_change(self.get_selected_engine())

    def get_selected_engine(self) -> EngineType:
        choice = self.engine_var.get()
        if "Native" in choice:
            return EngineType.NATIVE
        elif "LibreOffice" in choice:
            return EngineType.LIBREOFFICE
        elif "Microsoft" in choice:
            return EngineType.MSOFFICE
        return EngineType.AUTO

    def get_conversion_options(self) -> ConversionOptions:
        """Construct ConversionOptions from current UI values."""
        engine = self.get_selected_engine()
        quality = (
            PDFQuality.COMPRESSED
            if "Compressed" in self.quality_var.get()
            else PDFQuality.STANDARD
        )

        out_dir = None
        if not self.same_folder_var.get():
            path_str = self.dest_path_entry.get().strip()
            if path_str:
                out_dir = Path(path_str)

        slide_range = self.slide_range_entry.get().strip()
        if slide_range.lower() in ("all", ""):
            slide_range = None

        is_merge = self.mode_var.get() == "Merge All"
        merge_fn = self.merge_filename_entry.get().strip() or "merged_presentation.pdf"
        if not merge_fn.lower().endswith(".pdf"):
            merge_fn += ".pdf"

        return ConversionOptions(
            output_dir=out_dir,
            engine=engine,
            quality=quality,
            slide_range=slide_range,
            merge_all=is_merge,
            merge_filename=merge_fn,
            open_after_conversion=self.open_pdf_var.get(),
            open_folder_after=self.open_folder_var.get(),
        )
