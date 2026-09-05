"""Background QThread workers for non-blocking preview rendering and batch conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QMutex, QMutexLocker, QObject, QThread, Signal
from PySide6.QtGui import QPixmap

from paperize_gui.engine import PdfDocumentState, convert_pdf_file


class PreviewRenderTask:
    """Carries parameters for one preview render request."""

    def __init__(
        self,
        request_id: int,
        doc_state: PdfDocumentState,
        page_index: int,
        preset_name: str,
        strength: float,
        texture: float | None,
        vignette: float | None,
        dpi: int = 240,
    ):
        self.request_id = request_id
        self.doc_state = doc_state
        self.page_index = page_index
        self.preset_name = preset_name
        self.strength = strength
        self.texture = texture
        self.vignette = vignette
        self.dpi = dpi


class PreviewWorker(QThread):
    """Background worker rendering page previews without freezing the UI thread."""

    previewReady = Signal(int, QPixmap, QPixmap)  # request_id, original, paperized
    previewFailed = Signal(int, str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._pending_task: PreviewRenderTask | None = None
        self._is_running = True

    def submit(self, task: PreviewRenderTask) -> None:
        """Submit or replace the latest pending render task."""
        with QMutexLocker(self._mutex):
            self._pending_task = task
        if not self.isRunning():
            self.start()

    def stop(self) -> None:
        """Stop worker execution cleanly."""
        with QMutexLocker(self._mutex):
            self._is_running = False
            self._pending_task = None
        self.wait(1000)

    def run(self) -> None:
        while True:
            task: PreviewRenderTask | None = None
            with QMutexLocker(self._mutex):
                if not self._is_running:
                    break
                if self._pending_task:
                    task = self._pending_task
                    self._pending_task = None  # Consume task
                else:
                    break  # Nothing pending, thread exits; will be restarted on submit()

            if task:
                try:
                    orig_pix = task.doc_state.render_original_page(task.page_index, dpi=task.dpi)
                    paper_pix = task.doc_state.render_paperized_page(
                        page_index=task.page_index,
                        preset_name=task.preset_name,
                        strength=task.strength,
                        texture=task.texture,
                        vignette=task.vignette,
                        dpi=task.dpi,
                    )
                    self.previewReady.emit(task.request_id, orig_pix, paper_pix)
                except Exception as exc:
                    self.previewFailed.emit(task.request_id, str(exc))


class BatchProcessWorker(QThread):
    """Background worker converting multiple PDF documents in batch."""

    fileStarted = Signal(str, int, int)  # filename, current_index, total
    fileFinished = Signal(str, str)  # input_path, output_path
    overallProgress = Signal(int)  # 0 - 100 percentage
    allFinished = Signal(list)  # list of successfully converted files
    fileFailed = Signal(str, str)  # file, error message

    def __init__(
        self,
        files: Sequence[Path | str],
        output_dir: Path | str | None,
        suffix: str = "-paperized",
        preset_name: str = "parchment",
        strength: float = 1.0,
        texture: float | None = None,
        vignette: float | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.files = [Path(f).resolve() for f in files]
        self.output_dir = Path(output_dir).resolve() if output_dir else None
        self.suffix = suffix
        self.preset_name = preset_name
        self.strength = strength
        self.texture = texture
        self.vignette = vignette
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        total = len(self.files)
        completed: list[str] = []

        for idx, src_file in enumerate(self.files):
            if self._cancelled:
                break

            self.fileStarted.emit(src_file.name, idx + 1, total)

            # Determine output path
            if self.output_dir:
                dest_dir = self.output_dir
            else:
                dest_dir = src_file.parent

            dest_filename = f"{src_file.stem}{self.suffix}{src_file.suffix}"
            dest_path = dest_dir / dest_filename

            try:
                out_result = convert_pdf_file(
                    source=src_file,
                    output=dest_path,
                    preset_name=self.preset_name,
                    strength=self.strength,
                    texture=self.texture,
                    vignette=self.vignette,
                    force=True,
                )
                completed.append(str(out_result))
                self.fileFinished.emit(str(src_file), str(out_result))
            except Exception as exc:
                self.fileFailed.emit(str(src_file), str(exc))

            progress_percent = int(((idx + 1) / total) * 100)
            self.overallProgress.emit(progress_percent)

        self.allFinished.emit(completed)
