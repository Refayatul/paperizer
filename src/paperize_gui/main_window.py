"""Minimal, quiet main window for Paperize GUI inspired by Humanitas Labs' Paper."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QEvent, QPoint, QSize, QTimer, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QIcon,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from paperize_gui.engine import PdfDocumentState, convert_pdf_file
from paperize_gui.split_view import SplitPreviewCanvas, ViewMode
from paperize_gui.workers import PreviewRenderTask, PreviewWorker


class FloatingPillDock(QFrame):
    """Floating translucent control capsule at the bottom of the window."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("FloatingPillDock")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Drop shadow for floating depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 110))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)

        self.setStyleSheet(
            """
            #FloatingPillDock {
                background-color: rgba(26, 26, 28, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 22px;
            }
            QPushButton {
                background: transparent;
                color: #B0B0B5;
                border: none;
                border-radius: 14px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.10);
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: rgba(255, 255, 255, 0.18);
                color: #FFFFFF;
                font-weight: 600;
            }
            QPushButton#exportBtn {
                background-color: #D97706;
                color: #FFFFFF;
                font-weight: 600;
                padding: 5px 14px;
            }
            QPushButton#exportBtn:hover {
                background-color: #B45309;
            }
            QLabel {
                color: #8E8E93;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #D97706;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            """
        )


class MainWindow(QMainWindow):
    """Quiet, distraction-free window dedicated entirely to the document."""

    def __init__(self, initial_file: str | None = None):
        super().__init__()
        self.setWindowTitle("Paperize")
        self.resize(1180, 840)
        self.setAcceptDrops(True)

        self.current_doc_state: PdfDocumentState | None = None
        self.current_page_index: int = 0
        self._current_request_id: int = 0

        # Debounce timer for smooth slider changes
        self._preview_debounce_timer = QTimer(self)
        self._preview_debounce_timer.setSingleShot(True)
        self._preview_debounce_timer.setInterval(120)
        self._preview_debounce_timer.timeout.connect(self._trigger_preview_render)

        # Asynchronous worker
        self.preview_worker = PreviewWorker(self)
        self.preview_worker.previewReady.connect(self._on_preview_ready)
        self.preview_worker.previewFailed.connect(self._on_preview_failed)

        self._init_ui()
        self._setup_shortcuts()

        if initial_file and Path(initial_file).exists():
            self.load_pdf(Path(initial_file))

    def _init_ui(self) -> None:
        # Central container holding full-bleed canvas and floating island dock
        self.central_container = QWidget(self)
        self.setCentralWidget(self.central_container)

        # Canvas
        self.canvas = SplitPreviewCanvas(self.central_container)

        # Floating Bottom Island
        self.pill_dock = FloatingPillDock(self.central_container)
        pill_layout = QHBoxLayout(self.pill_dock)
        pill_layout.setContentsMargins(14, 6, 14, 6)
        pill_layout.setSpacing(10)

        # Open button
        self.btn_open = QPushButton("Open")
        self.btn_open.setToolTip("Open PDF (Ctrl+O)")
        self.btn_open.clicked.connect(self._on_open_file_dialog)
        pill_layout.addWidget(self.btn_open)

        pill_layout.addWidget(self._create_divider())

        # Presets Group
        self.preset_group = QButtonGroup(self)
        self.btn_parchment = QPushButton("Parchment")
        self.btn_parchment.setCheckable(True)
        self.btn_parchment.setChecked(True)
        self.btn_parchment.clicked.connect(self._request_preview_render)
        self.preset_group.addButton(self.btn_parchment)
        pill_layout.addWidget(self.btn_parchment)

        self.btn_cream = QPushButton("Cream")
        self.btn_cream.setCheckable(True)
        self.btn_cream.clicked.connect(self._request_preview_render)
        self.preset_group.addButton(self.btn_cream)
        pill_layout.addWidget(self.btn_cream)

        self.btn_sepia = QPushButton("Sepia")
        self.btn_sepia.setCheckable(True)
        self.btn_sepia.clicked.connect(self._request_preview_render)
        self.preset_group.addButton(self.btn_sepia)
        pill_layout.addWidget(self.btn_sepia)

        pill_layout.addWidget(self._create_divider())

        # View Mode Toggle: Split / Paper / White
        self.view_group = QButtonGroup(self)
        self.btn_mode_split = QPushButton("Split")
        self.btn_mode_split.setCheckable(True)
        self.btn_mode_split.setChecked(True)
        self.btn_mode_split.clicked.connect(lambda: self.canvas.set_view_mode(ViewMode.SPLIT))
        self.view_group.addButton(self.btn_mode_split)
        pill_layout.addWidget(self.btn_mode_split)

        self.btn_mode_paper = QPushButton("Paper")
        self.btn_mode_paper.setCheckable(True)
        self.btn_mode_paper.clicked.connect(lambda: self.canvas.set_view_mode(ViewMode.PAPERIZED))
        self.view_group.addButton(self.btn_mode_paper)
        pill_layout.addWidget(self.btn_mode_paper)

        pill_layout.addWidget(self._create_divider())

        # Warmth Slider
        lbl_warmth = QLabel("Warmth")
        pill_layout.addWidget(lbl_warmth)
        self.slider_warmth = QSlider(Qt.Orientation.Horizontal)
        self.slider_warmth.setRange(20, 100)
        self.slider_warmth.setValue(100)
        self.slider_warmth.setFixedWidth(70)
        self.slider_warmth.setToolTip("Warmth Strength")
        self.slider_warmth.valueChanged.connect(lambda: self._preview_debounce_timer.start())
        pill_layout.addWidget(self.slider_warmth)

        pill_layout.addWidget(self._create_divider())

        # Page Controls
        self.btn_prev = QPushButton("‹")
        self.btn_prev.setFixedWidth(26)
        self.btn_prev.setToolTip("Previous Page (Left / Backspace)")
        self.btn_prev.clicked.connect(lambda: self._go_to_page(self.current_page_index - 1))
        pill_layout.addWidget(self.btn_prev)

        self.lbl_pages = QLabel("0 / 0")
        self.lbl_pages.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill_layout.addWidget(self.lbl_pages)

        self.btn_next = QPushButton("›")
        self.btn_next.setFixedWidth(26)
        self.btn_next.setToolTip("Next Page (Right / Space)")
        self.btn_next.clicked.connect(lambda: self._go_to_page(self.current_page_index + 1))
        pill_layout.addWidget(self.btn_next)

        pill_layout.addWidget(self._create_divider())

        # Export Action
        self.btn_export = QPushButton("Export")
        self.btn_export.setObjectName("exportBtn")
        self.btn_export.setToolTip("Export Document (Ctrl+S)")
        self.btn_export.clicked.connect(self._export_current_document)
        pill_layout.addWidget(self.btn_export)

        self.pill_dock.adjustSize()

    def _create_divider(self) -> QWidget:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setStyleSheet("color: rgba(255, 255, 255, 0.15); max-height: 18px;")
        return div

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Position canvas full bleed
        self.canvas.setGeometry(0, 0, self.width(), self.height())

        # Center floating pill dock horizontally at the bottom
        dock_w = self.pill_dock.sizeHint().width()
        dock_h = self.pill_dock.sizeHint().height()
        pos_x = (self.width() - dock_w) // 2
        pos_y = self.height() - dock_h - 24
        self.pill_dock.setGeometry(pos_x, pos_y, dock_w, dock_h)

    def _setup_shortcuts(self) -> None:
        # File shortcuts
        QShortcut(QKeySequence("Ctrl+O"), self, self._on_open_file_dialog)
        QShortcut(QKeySequence("Ctrl+S"), self, self._export_current_document)

        # Page navigation
        QShortcut(QKeySequence("Space"), self, lambda: self._go_to_page(self.current_page_index + 1))
        QShortcut(QKeySequence("Right"), self, lambda: self._go_to_page(self.current_page_index + 1))
        QShortcut(QKeySequence("Left"), self, lambda: self._go_to_page(self.current_page_index - 1))
        QShortcut(QKeySequence("Backspace"), self, lambda: self._go_to_page(self.current_page_index - 1))

        # Presets (1, 2, 3)
        QShortcut(QKeySequence("1"), self, lambda: self._activate_preset("parchment"))
        QShortcut(QKeySequence("2"), self, lambda: self._activate_preset("cream"))
        QShortcut(QKeySequence("3"), self, lambda: self._activate_preset("sepia"))

        # Toggle view mode
        QShortcut(QKeySequence("Tab"), self, self._cycle_view_mode)

    def _activate_preset(self, name: str) -> None:
        if name == "parchment":
            self.btn_parchment.setChecked(True)
        elif name == "cream":
            self.btn_cream.setChecked(True)
        elif name == "sepia":
            self.btn_sepia.setChecked(True)
        self._request_preview_render()

    def _cycle_view_mode(self) -> None:
        if self.btn_mode_split.isChecked():
            self.btn_mode_paper.setChecked(True)
            self.canvas.set_view_mode(ViewMode.PAPERIZED)
        else:
            self.btn_mode_split.setChecked(True)
            self.canvas.set_view_mode(ViewMode.SPLIT)

    def load_pdf(self, path: Path) -> None:
        """Load a PDF document quietly and render first page."""
        try:
            if self.current_doc_state:
                self.current_doc_state.close()

            self.current_doc_state = PdfDocumentState(path)
            self.current_page_index = 0
            self.lbl_pages.setText(f"1 / {self.current_doc_state.page_count}")
            self.setWindowTitle(f"Paperize — {path.stem}")

            self._request_preview_render()
            self.canvas.reset_view()

        except Exception as exc:
            QMessageBox.critical(self, "Could Not Open", f"Unable to open '{path.name}':\n{exc}")

    def _go_to_page(self, index: int) -> None:
        if not self.current_doc_state:
            return
        clamped = max(0, min(index, self.current_doc_state.page_count - 1))
        if clamped != self.current_page_index:
            self.current_page_index = clamped
            self.lbl_pages.setText(f"{self.current_page_index + 1} / {self.current_doc_state.page_count}")
            self._request_preview_render()

    def _get_active_preset_name(self) -> str:
        if self.btn_cream.isChecked():
            return "cream"
        elif self.btn_sepia.isChecked():
            return "sepia"
        return "parchment"

    def _request_preview_render(self) -> None:
        self._preview_debounce_timer.start()

    def _trigger_preview_render(self) -> None:
        if not self.current_doc_state:
            return

        self._current_request_id += 1
        task = PreviewRenderTask(
            request_id=self._current_request_id,
            doc_state=self.current_doc_state,
            page_index=self.current_page_index,
            preset_name=self._get_active_preset_name(),
            strength=self.slider_warmth.value() / 100.0,
            texture=0.10,
            vignette=1.0,
        )
        self.preview_worker.submit(task)

    def _on_preview_ready(self, req_id: int, orig_pix, paper_pix) -> None:
        if req_id == self._current_request_id:
            self.canvas.set_pixmaps(orig_pix, paper_pix)

    def _on_preview_failed(self, req_id: int, error_msg: str) -> None:
        pass

    def _export_current_document(self) -> None:
        if not self.current_doc_state:
            return

        src_path = self.current_doc_state.file_path
        default_out = src_path.parent / f"{src_path.stem}-paperized{src_path.suffix}"

        out_file, _ = QFileDialog.getSaveFileName(
            self,
            "Export Paperized PDF",
            str(default_out),
            "PDF Files (*.pdf)",
        )
        if not out_file:
            return

        try:
            result = convert_pdf_file(
                source=src_path,
                output=Path(out_file),
                preset_name=self._get_active_preset_name(),
                strength=self.slider_warmth.value() / 100.0,
                texture=0.10,
                vignette=1.0,
                force=True,
            )
            QMessageBox.information(self, "Saved", f"Exported warm paper document to:\n{result.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not save:\n{exc}")

    def _on_open_file_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF Document",
            QDir.homePath(),
            "PDF Files (*.pdf)",
        )
        if file_path:
            self.load_pdf(Path(file_path))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() == ".pdf" and p.exists():
                self.load_pdf(p)
                event.acceptProposedAction()
                return

    def closeEvent(self, event) -> None:
        if self.preview_worker:
            self.preview_worker.stop()
        if self.current_doc_state:
            self.current_doc_state.close()
        event.accept()
