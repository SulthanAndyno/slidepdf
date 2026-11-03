"""Theme, color schemes, and styling constants for SlidePDF Studio GUI."""

from __future__ import annotations

# Color Palette
COLOR_PRIMARY = "#1f6aa5"          # Deep modern blue
COLOR_PRIMARY_HOVER = "#144870"
COLOR_ACCENT = "#2ecc71"           # Vibrant green for success / start
COLOR_ACCENT_HOVER = "#27ae60"
COLOR_DANGER = "#e74c3c"           # Red for cancel / remove
COLOR_DANGER_HOVER = "#c0392b"
COLOR_WARNING = "#f39c12"          # Amber / yellow for warnings

# Background & Frame Colors
COLOR_DARK_BG = "#121212"
COLOR_DARK_CARD = "#1e1e1e"
COLOR_DARK_CARD_HOVER = "#2a2a2a"
COLOR_DARK_BORDER = "#333333"

COLOR_LIGHT_BG = "#f4f6f9"
COLOR_LIGHT_CARD = "#ffffff"
COLOR_LIGHT_CARD_HOVER = "#f0f2f5"
COLOR_LIGHT_BORDER = "#e1e4e8"

# Text Colors
COLOR_TEXT_PRIMARY = ("#1a1a1a", "#ffffff")
COLOR_TEXT_SECONDARY = ("#666666", "#a0a0a0")
COLOR_TEXT_MUTED = ("#999999", "#777777")

# Badges & Status Colors
STATUS_COLORS = {
    "pending": ("#6c757d", "#495057"),
    "analyzing": ("#17a2b8", "#117a8b"),
    "processing": ("#007bff", "#0056b3"),
    "completed": ("#28a745", "#1e7e34"),
    "failed": ("#dc3545", "#bd2130"),
    "cancelled": ("#ffc107", "#d39e00"),
}

# Fonts
FONT_FAMILY = "Segoe UI" if "win" in __import__("sys").platform else "Inter"
FONT_TITLE = (FONT_FAMILY, 18, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_MONO = ("Consolas" if "win" in __import__("sys").platform else "monospace", 10)
