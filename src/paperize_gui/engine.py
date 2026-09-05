"""Core engine wrapping paperize and pymupdf for GUI previewing and conversion."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

import pymupdf
from PySide6.QtGui import QImage, QPixmap
from paperize.config import TransformRequest, UnitAmount
from paperize.pdf import paperize
from paperize.presets import PRESETS, get_preset


def pixmap_from_pymupdf(pix: pymupdf.Pixmap) -> QPixmap:
    """Convert a PyMuPDF Pixmap to a QPixmap safely."""
    img = QImage()
    img.loadFromData(pix.tobytes("png"))
    return QPixmap.fromImage(img)


class PdfDocumentState:
    """Manages an opened PDF document for navigation and previewing."""

    def __init__(self, file_path: Path | str):
        self.file_path = Path(file_path).resolve()
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        self.doc = pymupdf.open(str(self.file_path))
        self.page_count = len(self.doc)
        self.current_page = 0

    def close(self) -> None:
        """Close the open PyMuPDF document handle."""
        if self.doc and not self.doc.is_closed:
            self.doc.close()

    def render_original_page(self, page_index: int, dpi: int = 240) -> QPixmap:
        """Render the original unmodified page as a QPixmap."""
        if not (0 <= page_index < self.page_count):
            raise IndexError(f"Page index {page_index} out of bounds (0-{self.page_count - 1})")
        page = self.doc[page_index]
        pix = page.get_pixmap(dpi=dpi)
        return pixmap_from_pymupdf(pix)

    def render_paperized_page(
        self,
        page_index: int,
        preset_name: str = "parchment",
        strength: float = 1.0,
        texture: float | None = None,
        vignette: float | None = None,
        dpi: int = 240,
    ) -> QPixmap:
        """Extract a single page, transform it with paperize, and render as QPixmap."""
        if not (0 <= page_index < self.page_count):
            raise IndexError(f"Page index {page_index} out of bounds")

        with tempfile.TemporaryDirectory() as tmpdir:
            single_page_pdf = Path(tmpdir) / f"page_{page_index}.pdf"
            output_page_pdf = Path(tmpdir) / f"page_{page_index}_paperized.pdf"

            single_doc = pymupdf.open()
            single_doc.insert_pdf(self.doc, from_page=page_index, to_page=page_index)
            single_doc.save(str(single_page_pdf))
            single_doc.close()

            strength_amt = UnitAmount(min(max(float(strength), 0.0), 1.0))
            texture_amt = UnitAmount(min(max(float(texture), 0.0), 1.0)) if texture is not None else None
            vignette_amt = UnitAmount(min(max(float(vignette), 0.0), 1.0)) if vignette is not None else None

            request = TransformRequest(
                source=single_page_pdf,
                output=output_page_pdf,
                preset_name=preset_name,
                strength=strength_amt,
                texture=texture_amt,
                vignette=vignette_amt,
                force=True,
            )
            paperize(request)

            temp_doc = pymupdf.open(str(output_page_pdf))
            pix = temp_doc[0].get_pixmap(dpi=dpi)
            temp_doc.close()

            return pixmap_from_pymupdf(pix)


def convert_pdf_file(
    source: Path | str,
    output: Path | str,
    preset_name: str = "parchment",
    strength: float = 1.0,
    texture: float | None = None,
    vignette: float | None = None,
    force: bool = True,
) -> Path:
    """Paperize a complete document to the destination path."""
    source_path = Path(source).resolve()
    output_path = Path(output).resolve()

    strength_amt = UnitAmount(min(max(float(strength), 0.0), 1.0))
    texture_amt = UnitAmount(min(max(float(texture), 0.0), 1.0)) if texture is not None else None
    vignette_amt = UnitAmount(min(max(float(vignette), 0.0), 1.0)) if vignette is not None else None

    req = TransformRequest(
        source=source_path,
        output=output_path,
        preset_name=preset_name,
        strength=strength_amt,
        texture=texture_amt,
        vignette=vignette_amt,
        force=force,
    )
    return paperize(req)
