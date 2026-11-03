"""Collapsible Log Console Drawer widget."""

from __future__ import annotations

import datetime
from typing import Optional
import customtkinter as ctk

from slidepdf.ui import theme


class LogDrawer(ctk.CTkFrame):
    """Expandable log console displaying runtime activity and debug messages."""

    def __init__(self, master, default_open: bool = False, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.is_expanded = default_open

        self._build_ui()

    def _build_ui(self) -> None:
        # Header bar
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.header.pack(fill="x", padx=10, pady=(6, 4))

        self.toggle_btn = ctk.CTkButton(
            self.header,
            text="Console Logs ▼ (Ctrl+L)" if not self.is_expanded else "Console Logs ▲ (Ctrl+L)",
            font=theme.FONT_SMALL,
            fg_color="transparent",
            text_color="#aaaaaa",
            hover_color="#333333",
            width=150,
            command=self.toggle,
        )
        self.toggle_btn.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self.header,
            text="Clear",
            font=theme.FONT_SMALL,
            width=50,
            height=22,
            fg_color="transparent",
            hover_color="#444444",
            command=self.clear,
        )
        self.clear_btn.pack(side="right", padx=4)

        # Log content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        if self.is_expanded:
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.textbox = ctk.CTkTextbox(
            self.content_frame,
            font=theme.FONT_MONO,
            height=120,
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.configure(state="disabled")

    def toggle(self) -> None:
        """Toggle console expansion."""
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
            self.toggle_btn.configure(text="Console Logs ▲")
        else:
            self.content_frame.pack_forget()
            self.toggle_btn.configure(text="Console Logs ▼")

    def log(self, message: str, level: str = "INFO") -> None:
        """Append a message to the log drawer."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", formatted)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        """Clear the console text."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
