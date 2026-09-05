"""Application entry point and desktop integration for Paperize GUI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from paperize_gui.main_window import MainWindow


def main() -> None:
    """Launch the Paperize GUI application."""
    # Ensure smooth Wayland / X11 rendering
    if "QT_QPA_PLATFORM" not in os.environ:
        # Default to wayland with xcb fallback on Linux
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("paperize-gui")
    app.setApplicationDisplayName("Paperize")
    app.setOrganizationName("Humanitas Labs & Kai")
    app.setDesktopFileName("paperize-gui")

    # Load Vector Icon
    base_dir = Path(__file__).resolve().parent.parent.parent
    icon_path = base_dir / "assets" / "icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Parse initial file argument if passed
    initial_file: str | None = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        arg_path = Path(sys.argv[1])
        if arg_path.exists() and arg_path.suffix.lower() == ".pdf":
            initial_file = str(arg_path)

    window = MainWindow(initial_file=initial_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
