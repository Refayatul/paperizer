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
    """Launch the Paperizer application."""
    # Ensure smooth Wayland / X11 rendering on Linux and silence portal noise
    if sys.platform.startswith("linux"):
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
    if "QT_LOGGING_RULES" not in os.environ:
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.services=false"

    # Set explicit Windows AppUserModelID for taskbar icon grouping
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("HumanitasLabs.Paperizer.App")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("paperizer")
    app.setApplicationDisplayName("Paperizer")
    app.setOrganizationName("Humanitas Labs & Kai")
    app.setDesktopFileName("paperizer")

    # Locate application icon (works in dev, installed wheel, or PyInstaller frozen bundle)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    elif getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent.parent.parent

    icon_path = base_dir / "assets" / ("icon.ico" if sys.platform == "win32" else "icon.svg")
    if not icon_path.exists():
        icon_path = base_dir / "assets" / "icon.svg"
    if not icon_path.exists():
        icon_path = base_dir / "assets" / "icon.ico"
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
