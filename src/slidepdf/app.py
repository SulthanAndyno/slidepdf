"""Main desktop application entrypoint for SlidePDF Studio."""

from __future__ import annotations

import sys
import customtkinter as ctk

from slidepdf.ui.main_window import MainWindow


def main() -> None:
    """Launch the SlidePDF Studio Desktop Application or handle CLI."""
    # If invoked with CLI subcommands or help flags, route to CLI directly
    cli_commands = {"convert", "batch", "doctor", "--help", "-h", "--version", "-v"}
    if len(sys.argv) > 1 and sys.argv[1].lower() in cli_commands:
        from slidepdf.cli import main as cli_main
        cli_main()
        return

    # Set appearance & theme
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Start main application loop
    app = MainWindow()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
