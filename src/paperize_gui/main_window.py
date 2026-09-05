"""Main application window for Paperize GUI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QFileInfo, QTimer, Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from paperize_gui.engine import PdfDocumentState, convert_pdf_file
from paperize_gui.split_view import SplitPreviewCanvas, ViewMode
from paperize_gui.workers import BatchProcessWorker, PreviewRenderTask, PreviewWorker


class MainWindow(QMainWindow):
    """Primary window coordinating PDF loading, preview rendering, and batch processing."""

    def __init__(self, initial_file: str | None = None):
        super().__init__()
        self.setWindowTitle("Paperize — PDF Eye-Comfort & Paper Styler")
        self.resize(1240, 840)
        self.setAcceptDrops(True)

        self.current_doc_state: PdfDocumentState | None = None
        self.current_page_index: int = 0
        self._current_request_id: int = 0

        # Debounce timer for preview updates when sliders are dragged
        self._preview_debounce_timer = QTimer(self)
        self._preview_debounce_timer.setSingleShot(True)
        self._preview_debounce_timer.setInterval(120)
        self._preview_debounce_timer.timeout.connect(self._trigger_preview_render)

        # Worker threads
        self.preview_worker = PreviewWorker(self)
        self.preview_worker.previewReady.connect(self._on_preview_ready)
        self.preview_worker.previewFailed.connect(self._on_preview_failed)

        self.batch_worker: BatchProcessWorker | None = None

        self._init_ui()

        if initial_file and Path(initial_file).exists():
            self.load_pdf(Path(initial_file))

    def _init_ui(self) -> None:
        self.canvas = SplitPreviewCanvas(self)
        self._create_toolbar()

        # Central widget with splitter between Canvas and Sidebar
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left Container: Canvas + Bottom Page Navigation
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(6)

        canvas_layout.addWidget(self.canvas, stretch=1)

        bottom_bar = self._create_page_navigation_bar()
        canvas_layout.addWidget(bottom_bar)

        splitter.addWidget(canvas_container)

        # Right Container: Sidebar with Tabs (Style & Batch)
        sidebar = self._create_sidebar()
        sidebar.setMaximumWidth(380)
        sidebar.setMinimumWidth(320)
        splitter.addWidget(sidebar)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        # Status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drop a PDF to begin.")

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Controls", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File actions
        open_action = QAction("Open PDF", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setToolTip("Open a PDF document (Ctrl+O)")
        open_action.triggered.connect(self._on_open_file_dialog)
        toolbar.addAction(open_action)

        add_batch_action = QAction("Add to Batch", self)
        add_batch_action.setToolTip("Add multiple PDFs to batch conversion list")
        add_batch_action.triggered.connect(self._on_add_batch_dialog)
        toolbar.addAction(add_batch_action)

        toolbar.addSeparator()

        # View Mode Buttons
        view_group = QButtonGroup(self)
        
        self.btn_split = QPushButton("Split View")
        self.btn_split.setCheckable(True)
        self.btn_split.setChecked(True)
        self.btn_split.clicked.connect(lambda: self.canvas.set_view_mode(ViewMode.SPLIT))
        view_group.addButton(self.btn_split)
        toolbar.addWidget(self.btn_split)

        self.btn_side = QPushButton("Side-by-Side")
        self.btn_side.setCheckable(True)
        self.btn_side.clicked.connect(lambda: self.canvas.set_view_mode(ViewMode.SIDE_BY_SIDE))
        view_group.addButton(self.btn_side)
        toolbar.addWidget(self.btn_side)

        self.btn_paper = QPushButton("Paperized")
        self.btn_paper.setCheckable(True)
        self.btn_paper.clicked.connect(lambda: self.canvas.set_view_mode(ViewMode.PAPERIZED))
        view_group.addButton(self.btn_paper)
        toolbar.addWidget(self.btn_paper)

        self.btn_orig = QPushButton("Original")
        self.btn_orig.setCheckable(True)
        self.btn_orig.clicked.connect(lambda: self.canvas.set_view_mode(ViewMode.ORIGINAL))
        view_group.addButton(self.btn_orig)
        toolbar.addWidget(self.btn_orig)

        toolbar.addSeparator()

        # Zoom Actions
        zoom_out_act = QAction("Zoom Out", self)
        zoom_out_act.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_act.triggered.connect(self.canvas.zoom_out)
        toolbar.addAction(zoom_out_act)

        self.lbl_zoom = QLabel(" 100% ")
        toolbar.addWidget(self.lbl_zoom)
        self.canvas.zoomChanged.connect(lambda z: self.lbl_zoom.setText(f" {int(z * 100)}% "))

        zoom_in_act = QAction("Zoom In", self)
        zoom_in_act.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_act.triggered.connect(self.canvas.zoom_in)
        toolbar.addAction(zoom_in_act)

        fit_page_act = QAction("Fit Page", self)
        fit_page_act.triggered.connect(self.canvas.fit_to_page)
        toolbar.addAction(fit_page_act)

        fit_width_act = QAction("Fit Width", self)
        fit_width_act.triggered.connect(self.canvas.fit_to_width)
        toolbar.addAction(fit_width_act)

        toolbar.addSeparator()

        # Quick Export Action
        export_act = QAction("Export This PDF", self)
        export_act.setShortcut(QKeySequence("Ctrl+S"))
        export_act.setToolTip("Export the current document with selected style (Ctrl+S)")
        export_act.triggered.connect(self._export_current_document)
        toolbar.addAction(export_act)

    def _create_page_navigation_bar(self) -> QWidget:
        bar = QFrame()
        bar.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.btn_first = QPushButton("⏮ First")
        self.btn_first.clicked.connect(lambda: self._go_to_page(0))
        layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setShortcut(QKeySequence.StandardKey.MoveToPreviousPage)
        self.btn_prev.clicked.connect(lambda: self._go_to_page(self.current_page_index - 1))
        layout.addWidget(self.btn_prev)

        layout.addSpacing(10)
        self.lbl_page_prefix = QLabel("Page")
        layout.addWidget(self.lbl_page_prefix)

        self.txt_page_num = QLineEdit("1")
        self.txt_page_num.setMaximumWidth(45)
        self.txt_page_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_page_num.returnPressed.connect(self._on_page_jump)
        layout.addWidget(self.txt_page_num)

        self.lbl_total_pages = QLabel("of 0")
        layout.addWidget(self.lbl_total_pages)
        layout.addSpacing(10)

        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setShortcut(QKeySequence.StandardKey.MoveToNextPage)
        self.btn_next.clicked.connect(lambda: self._go_to_page(self.current_page_index + 1))
        layout.addWidget(self.btn_next)

        self.btn_last = QPushButton("Last ⏭")
        self.btn_last.clicked.connect(self._go_to_last_page)
        layout.addWidget(self.btn_last)

        layout.addStretch()

        self.lbl_render_indicator = QLabel("")
        self.lbl_render_indicator.setStyleSheet("color: #E67E22; font-weight: bold;")
        layout.addWidget(self.lbl_render_indicator)

        return bar

    def _create_sidebar(self) -> QWidget:
        tabs = QTabWidget()

        # Tab 1: Style & Presets
        style_tab = QWidget()
        style_layout = QVBoxLayout(style_tab)
        style_layout.setContentsMargins(12, 12, 12, 12)
        style_layout.setSpacing(14)

        # Preset Radios
        preset_group = QGroupBox("Paper Style Preset")
        preset_vbox = QVBoxLayout(preset_group)

        self.radio_parchment = QRadioButton("Parchment (Warm Golden)")
        self.radio_parchment.setChecked(True)
        self.radio_parchment.toggled.connect(self._on_style_changed)
        preset_vbox.addWidget(self.radio_parchment)

        self.radio_cream = QRadioButton("Cream (Soft Ivory Reading)")
        self.radio_cream.toggled.connect(self._on_style_changed)
        preset_vbox.addWidget(self.radio_cream)

        self.radio_sepia = QRadioButton("Sepia (Antique Vintage)")
        self.radio_sepia.toggled.connect(self._on_style_changed)
        preset_vbox.addWidget(self.radio_sepia)

        style_layout.addWidget(preset_group)

        # Sliders Group
        slider_group = QGroupBox("Fine-Tuning Controls")
        slider_vbox = QVBoxLayout(slider_group)

        # Strength (Warmth)
        self.lbl_strength_title = QLabel("Warmth / Strength: 100%")
        slider_vbox.addWidget(self.lbl_strength_title)
        self.slider_strength = QSlider(Qt.Orientation.Horizontal)
        self.slider_strength.setRange(10, 100)
        self.slider_strength.setValue(100)
        self.slider_strength.valueChanged.connect(self._on_strength_slider_changed)
        slider_vbox.addWidget(self.slider_strength)

        # Texture
        self.lbl_texture_title = QLabel("Paper Texture Grain: 10%")
        slider_vbox.addWidget(self.lbl_texture_title)
        self.slider_texture = QSlider(Qt.Orientation.Horizontal)
        self.slider_texture.setRange(0, 50)
        self.slider_texture.setValue(10)
        self.slider_texture.valueChanged.connect(self._on_texture_slider_changed)
        slider_vbox.addWidget(self.slider_texture)

        # Vignette
        self.lbl_vignette_title = QLabel("Vignette Falloff: 100%")
        slider_vbox.addWidget(self.lbl_vignette_title)
        self.slider_vignette = QSlider(Qt.Orientation.Horizontal)
        self.slider_vignette.setRange(0, 100)
        self.slider_vignette.setValue(100)
        self.slider_vignette.valueChanged.connect(self._on_vignette_slider_changed)
        slider_vbox.addWidget(self.slider_vignette)

        style_layout.addWidget(slider_group)

        style_layout.addStretch()

        # Big Export Button
        self.btn_export_doc = QPushButton("Export Current PDF")
        self.btn_export_doc.setStyleSheet("font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_export_doc.clicked.connect(self._export_current_document)
        style_layout.addWidget(self.btn_export_doc)

        tabs.addTab(style_tab, "Document Style")

        # Tab 2: Batch Queue
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        batch_layout.setContentsMargins(12, 12, 12, 12)
        batch_layout.setSpacing(10)

        batch_info = QLabel("Drop files here or click Add Files to batch process multiple documents:")
        batch_info.setWordWrap(True)
        batch_layout.addWidget(batch_info)

        self.table_batch = QTableWidget(0, 2)
        self.table_batch.setHorizontalHeaderLabels(["Filename", "Status"])
        self.table_batch.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_batch.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        batch_layout.addWidget(self.table_batch)

        batch_btn_box = QHBoxLayout()
        btn_add_files = QPushButton("Add Files...")
        btn_add_files.clicked.connect(self._on_add_batch_dialog)
        batch_btn_box.addWidget(btn_add_files)

        btn_clear_batch = QPushButton("Clear")
        btn_clear_batch.clicked.connect(self._clear_batch_queue)
        batch_btn_box.addWidget(btn_clear_batch)
        batch_layout.addLayout(batch_btn_box)

        # Output folder options
        out_box = QGroupBox("Output Location")
        out_box_layout = QVBoxLayout(out_box)
        self.chk_same_folder = QCheckBox("Save alongside source files")
        self.chk_same_folder.setChecked(True)
        out_box_layout.addWidget(self.chk_same_folder)

        self.txt_output_dir = QLineEdit()
        self.txt_output_dir.setPlaceholderText("Custom output folder...")
        self.txt_output_dir.setEnabled(False)
        self.chk_same_folder.toggled.connect(lambda checked: self.txt_output_dir.setEnabled(not checked))
        out_box_layout.addWidget(self.txt_output_dir)

        batch_layout.addWidget(out_box)

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setValue(0)
        self.batch_progress_bar.setVisible(False)
        batch_layout.addWidget(self.batch_progress_bar)

        self.btn_start_batch = QPushButton("Convert All in Batch")
        self.btn_start_batch.setStyleSheet("font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_start_batch.clicked.connect(self._start_batch_conversion)
        batch_layout.addWidget(self.btn_start_batch)

        tabs.addTab(batch_tab, "Batch Queue")

        return tabs

    # Document Loading & Page Flipping
    def load_pdf(self, path: Path) -> None:
        """Load a PDF file and initialize preview."""
        try:
            if self.current_doc_state:
                self.current_doc_state.close()

            self.current_doc_state = PdfDocumentState(path)
            self.current_page_index = 0
            self.lbl_total_pages.setText(f"of {self.current_doc_state.page_count}")
            self.txt_page_num.setText("1")
            self.setWindowTitle(f"Paperize — {path.name}")
            self.status_bar.showMessage(f"Loaded {path.name} ({self.current_doc_state.page_count} pages)")

            # Add to batch queue automatically if not present
            self._add_path_to_batch(path)

            self._request_preview_render()
            self.canvas.reset_view()

        except Exception as exc:
            QMessageBox.critical(self, "Failed to Open PDF", f"Could not open '{path.name}':\n{exc}")

    def _go_to_page(self, index: int) -> None:
        if not self.current_doc_state:
            return
        clamped = max(0, min(index, self.current_doc_state.page_count - 1))
        if clamped != self.current_page_index:
            self.current_page_index = clamped
            self.txt_page_num.setText(str(self.current_page_index + 1))
            self._request_preview_render()

    def _go_to_last_page(self) -> None:
        if self.current_doc_state:
            self._go_to_page(self.current_doc_state.page_count - 1)

    def _on_page_jump(self) -> None:
        if not self.current_doc_state:
            return
        try:
            page_val = int(self.txt_page_num.text().strip())
            self._go_to_page(page_val - 1)
        except ValueError:
            self.txt_page_num.setText(str(self.current_page_index + 1))

    # Preset & Sliders Interaction
    def _get_active_preset_name(self) -> str:
        if self.radio_cream.isChecked():
            return "cream"
        elif self.radio_sepia.isChecked():
            return "sepia"
        return "parchment"

    def _on_style_changed(self) -> None:
        self._request_preview_render()

    def _on_strength_slider_changed(self, val: int) -> None:
        self.lbl_strength_title.setText(f"Warmth / Strength: {val}%")
        self._preview_debounce_timer.start()

    def _on_texture_slider_changed(self, val: int) -> None:
        self.lbl_texture_title.setText(f"Paper Texture Grain: {val}%")
        self._preview_debounce_timer.start()

    def _on_vignette_slider_changed(self, val: int) -> None:
        self.lbl_vignette_title.setText(f"Vignette Falloff: {val}%")
        self._preview_debounce_timer.start()

    def _request_preview_render(self) -> None:
        self._preview_debounce_timer.start()

    def _trigger_preview_render(self) -> None:
        if not self.current_doc_state:
            return

        self._current_request_id += 1
        self.lbl_render_indicator.setText("Rendering preview...")

        task = PreviewRenderTask(
            request_id=self._current_request_id,
            doc_state=self.current_doc_state,
            page_index=self.current_page_index,
            preset_name=self._get_active_preset_name(),
            strength=self.slider_strength.value() / 100.0,
            texture=self.slider_texture.value() / 100.0,
            vignette=self.slider_vignette.value() / 100.0,
        )
        self.preview_worker.submit(task)

    def _on_preview_ready(self, req_id: int, orig_pix, paper_pix) -> None:
        if req_id == self._current_request_id:
            self.canvas.set_pixmaps(orig_pix, paper_pix)
            self.lbl_render_indicator.setText("")

    def _on_preview_failed(self, req_id: int, error_msg: str) -> None:
        if req_id == self._current_request_id:
            self.lbl_render_indicator.setText("Preview error")
            self.status_bar.showMessage(f"Preview rendering failed: {error_msg}")

    # File Export
    def _export_current_document(self) -> None:
        if not self.current_doc_state:
            QMessageBox.information(self, "No Document", "Please open a PDF document first.")
            return

        src_path = self.current_doc_state.file_path
        default_out = src_path.parent / f"{src_path.stem}-paperized{src_path.suffix}"

        out_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Paperized PDF",
            str(default_out),
            "PDF Files (*.pdf)",
        )
        if not out_file:
            return

        self.status_bar.showMessage(f"Exporting '{Path(out_file).name}'...")
        try:
            result = convert_pdf_file(
                source=src_path,
                output=Path(out_file),
                preset_name=self._get_active_preset_name(),
                strength=self.slider_strength.value() / 100.0,
                texture=self.slider_texture.value() / 100.0,
                vignette=self.slider_vignette.value() / 100.0,
                force=True,
            )
            self.status_bar.showMessage(f"Successfully exported: {result.name}")
            QMessageBox.information(self, "Export Complete", f"Saved paperized PDF to:\n{result}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not export PDF:\n{exc}")

    # Batch Processing
    def _add_path_to_batch(self, path: Path) -> None:
        for r in range(self.table_batch.rowCount()):
            item = self.table_batch.item(r, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(path):
                return  # already in table

        row = self.table_batch.rowCount()
        self.table_batch.insertRow(row)

        name_item = QTableWidgetItem(path.name)
        name_item.setData(Qt.ItemDataRole.UserRole, str(path))
        self.table_batch.setItem(row, 0, name_item)

        status_item = QTableWidgetItem("Ready")
        self.table_batch.setItem(row, 1, status_item)

    def _clear_batch_queue(self) -> None:
        self.table_batch.setRowCount(0)

    def _start_batch_conversion(self) -> None:
        rows = self.table_batch.rowCount()
        if rows == 0:
            QMessageBox.information(self, "Batch Empty", "No files in the batch queue.")
            return

        files = []
        for r in range(rows):
            item = self.table_batch.item(r, 0)
            if item:
                files.append(Path(item.data(Qt.ItemDataRole.UserRole)))
                self.table_batch.setItem(r, 1, QTableWidgetItem("Queued..."))

        out_dir = None if self.chk_same_folder.isChecked() else Path(self.txt_output_dir.text())

        self.batch_progress_bar.setVisible(True)
        self.batch_progress_bar.setValue(0)
        self.btn_start_batch.setEnabled(False)

        self.batch_worker = BatchProcessWorker(
            files=files,
            output_dir=out_dir,
            preset_name=self._get_active_preset_name(),
            strength=self.slider_strength.value() / 100.0,
            texture=self.slider_texture.value() / 100.0,
            vignette=self.slider_vignette.value() / 100.0,
            parent=self,
        )
        self.batch_worker.fileStarted.connect(self._on_batch_file_started)
        self.batch_worker.fileFinished.connect(self._on_batch_file_finished)
        self.batch_worker.fileFailed.connect(self._on_batch_file_failed)
        self.batch_worker.overallProgress.connect(self.batch_progress_bar.setValue)
        self.batch_worker.allFinished.connect(self._on_batch_all_finished)
        self.batch_worker.start()

    def _on_batch_file_started(self, name: str, cur: int, total: int) -> None:
        self.status_bar.showMessage(f"Processing ({cur}/{total}): {name}...")
        for r in range(self.table_batch.rowCount()):
            item = self.table_batch.item(r, 0)
            if item and item.text() == name:
                self.table_batch.setItem(r, 1, QTableWidgetItem("Processing..."))
                break

    def _on_batch_file_finished(self, src: str, dst: str) -> None:
        for r in range(self.table_batch.rowCount()):
            item = self.table_batch.item(r, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == src:
                self.table_batch.setItem(r, 1, QTableWidgetItem("✓ Done"))
                break

    def _on_batch_file_failed(self, src: str, err: str) -> None:
        for r in range(self.table_batch.rowCount()):
            item = self.table_batch.item(r, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == src:
                self.table_batch.setItem(r, 1, QTableWidgetItem("✗ Error"))
                break

    def _on_batch_all_finished(self, completed: list) -> None:
        self.btn_start_batch.setEnabled(True)
        self.batch_progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Batch completed: {len(completed)} file(s) transformed.")
        QMessageBox.information(
            self,
            "Batch Complete",
            f"Successfully transformed {len(completed)} PDF document(s).",
        )

    # Dialogs & Drag-and-Drop
    def _on_open_file_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF Document",
            QDir.homePath(),
            "PDF Files (*.pdf)",
        )
        if file_path:
            self.load_pdf(Path(file_path))

    def _on_add_batch_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDFs for Batch Conversion",
            QDir.homePath(),
            "PDF Files (*.pdf)",
        )
        for f in files:
            self._add_path_to_batch(Path(f))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent) -> None:
        pdf_paths = []
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() == ".pdf" and p.exists():
                pdf_paths.append(p)

        if pdf_paths:
            # Open first file for preview
            self.load_pdf(pdf_paths[0])
            # Add all dropped files to batch queue
            for p in pdf_paths:
                self._add_path_to_batch(p)
            event.acceptProposedAction()

    def closeEvent(self, event) -> None:
        if self.preview_worker:
            self.preview_worker.stop()
        if self.current_doc_state:
            self.current_doc_state.close()
        event.accept()
