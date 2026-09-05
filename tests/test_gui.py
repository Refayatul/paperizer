"""Automated tests for Paperize GUI engine, canvas, and main window."""

from pathlib import Path
import pymupdf
import pytest
from PySide6.QtWidgets import QApplication

from paperize_gui.engine import PdfDocumentState, convert_pdf_file
from paperize_gui.split_view import SplitPreviewCanvas, ViewMode
from paperize_gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "test_doc.pdf"
    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text((50, 50), f"Test Page {i + 1}", fontsize=18)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_pdf_document_state(qapp, sample_pdf: Path):
    state = PdfDocumentState(sample_pdf)
    assert state.page_count == 3
    
    orig = state.render_original_page(0, dpi=72)
    assert not orig.isNull()
    assert orig.width() > 0

    paper = state.render_paperized_page(0, preset_name="cream", strength=0.8, dpi=72)
    assert not paper.isNull()
    assert paper.width() > 0
    state.close()


def test_convert_pdf_file(sample_pdf: Path, tmp_path: Path):
    output_pdf = tmp_path / "converted.pdf"
    result = convert_pdf_file(
        source=sample_pdf,
        output=output_pdf,
        preset_name="sepia",
        strength=0.9,
    )
    assert result.exists()
    assert result.stat().st_size > 0

    # Verify converted PDF has same page count
    doc = pymupdf.open(str(result))
    assert len(doc) == 3
    doc.close()


def test_canvas_view_modes(qapp):
    canvas = SplitPreviewCanvas()
    canvas.resize(800, 600)
    
    canvas.set_view_mode(ViewMode.SPLIT)
    assert canvas._view_mode == ViewMode.SPLIT

    canvas.set_zoom(1.5)
    assert abs(canvas._zoom - 1.5) < 0.01

    canvas.zoom_in()
    assert canvas._zoom > 1.5

    canvas.zoom_out()
    assert canvas._zoom <= 1.5


def test_main_window_lifecycle(qapp, sample_pdf: Path):
    win = MainWindow(initial_file=str(sample_pdf))
    assert win.current_doc_state is not None
    assert win.current_doc_state.page_count == 3

    # Switch presets
    win.btn_sepia.setChecked(True)
    assert win._get_active_preset_name() == "sepia"

    win.btn_cream.setChecked(True)
    assert win._get_active_preset_name() == "cream"

    # Navigation
    win._go_to_page(1)
    assert win.current_page_index == 1

    win.close()


def test_canvas_reading_fit(qapp, sample_pdf: Path):
    state = PdfDocumentState(sample_pdf)
    orig = state.render_original_page(0, dpi=72)
    paper = state.render_paperized_page(0, preset_name="parchment", strength=0.85, dpi=72)

    canvas = SplitPreviewCanvas()
    canvas.resize(1200, 800)
    canvas.set_pixmaps(orig, paper)

    # Test fit_to_reading
    canvas.fit_to_reading()
    assert canvas._zoom > 0.2
    assert canvas._zoom <= 4.0

    # Test scroll_vertical
    initial_y = canvas._pan_offset.y()
    canvas.scroll_vertical(-100)
    assert canvas._pan_offset.y() == initial_y - 100

    state.close()

