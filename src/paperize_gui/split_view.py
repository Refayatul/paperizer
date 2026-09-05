"""Interactive Before/After split comparison canvas for PDF pages."""

from __future__ import annotations

from enum import Enum
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget


class ViewMode(Enum):
    SPLIT = "split"
    PAPERIZED = "paperized"
    ORIGINAL = "original"
    SIDE_BY_SIDE = "side_by_side"


class SplitPreviewCanvas(QWidget):
    """Interactive canvas supporting split curtain, side-by-side, and full page views."""

    zoomChanged = Signal(float)
    dividerMoved = Signal(float)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._original_pixmap: QPixmap | None = None
        self._paperized_pixmap: QPixmap | None = None

        self._split_fraction: float = 0.5  # 0.0 to 1.0 across page width
        self._is_dragging_divider: bool = False
        self._is_panning: bool = False
        self._pan_start_pos: QPointF = QPointF(0, 0)
        self._pan_offset: QPointF = QPointF(0, 0)

        self._zoom: float = 1.0  # 1.0 = 100%
        self._view_mode: ViewMode = ViewMode.SPLIT
        self._divider_hovered: bool = False
        self._page_shadow_color = QColor(0, 0, 0, 80)
        self._placeholder_text = "Drop a PDF to begin reading on paper\nor press Ctrl+O"

    def set_pixmaps(self, original: QPixmap | None, paperized: QPixmap | None) -> None:
        """Update both original and paperized pixmaps."""
        self._original_pixmap = original
        self._paperized_pixmap = paperized
        self.update()

    def set_view_mode(self, mode: ViewMode) -> None:
        """Switch view mode (SPLIT, PAPERIZED, ORIGINAL, SIDE_BY_SIDE)."""
        self._view_mode = mode
        self.update()

    def set_zoom(self, zoom: float) -> None:
        """Set zoom factor clamped between 0.2 and 4.0."""
        new_zoom = max(0.2, min(zoom, 4.0))
        if abs(new_zoom - self._zoom) > 0.001:
            self._zoom = new_zoom
            self.zoomChanged.emit(self._zoom)
            self.update()

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom * 1.2)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom / 1.2)

    def reset_view(self) -> None:
        """Center the page and reset pan/zoom."""
        self._pan_offset = QPointF(0, 0)
        self.fit_to_page()

    def fit_to_page(self) -> None:
        """Fit entire page comfortably within the viewport."""
        ref_pixmap = self._paperized_pixmap or self._original_pixmap
        if not ref_pixmap or ref_pixmap.isNull():
            return
        
        available_w = max(50, self.width() - 60)
        available_h = max(50, self.height() - 60)

        if self._view_mode == ViewMode.SIDE_BY_SIDE:
            scale_w = available_w / (ref_pixmap.width() * 2 + 30)
            scale_h = available_h / ref_pixmap.height()
        else:
            scale_w = available_w / ref_pixmap.width()
            scale_h = available_h / ref_pixmap.height()

        self._zoom = min(scale_w, scale_h, 1.5)
        self._pan_offset = QPointF(0, 0)
        self.zoomChanged.emit(self._zoom)
        self.update()

    def fit_to_width(self) -> None:
        """Fit page width to the viewport."""
        ref_pixmap = self._paperized_pixmap or self._original_pixmap
        if not ref_pixmap or ref_pixmap.isNull():
            return

        available_w = max(50, self.width() - 80)
        if self._view_mode == ViewMode.SIDE_BY_SIDE:
            self._zoom = available_w / (ref_pixmap.width() * 2 + 30)
        else:
            self._zoom = available_w / ref_pixmap.width()

        self._zoom = max(0.2, min(self._zoom, 3.0))
        self._pan_offset = QPointF(0, 0)
        self.zoomChanged.emit(self._zoom)
        self.update()

    def _get_page_rect(self) -> QRectF:
        """Calculate on-screen target rect for the rendered page."""
        ref_pixmap = self._paperized_pixmap or self._original_pixmap
        if not ref_pixmap or ref_pixmap.isNull():
            return QRectF()

        target_w = ref_pixmap.width() * self._zoom
        target_h = ref_pixmap.height() * self._zoom

        x = (self.width() - target_w) / 2.0 + self._pan_offset.x()
        y = (self.height() - target_h) / 2.0 + self._pan_offset.y()

        return QRectF(x, y, target_w, target_h)

    def _get_divider_screen_x(self, page_rect: QRectF) -> float:
        """Get the absolute X position of the split divider."""
        return page_rect.left() + page_rect.width() * self._split_fraction

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Background canvas color (KDE dark/neutral slate)
        palette = self.palette()
        bg_color = palette.window().color()
        darker_bg = bg_color.darker(115) if bg_color.lightness() > 128 else bg_color.lighter(115)
        painter.fillRect(self.rect(), darker_bg)

        ref_pixmap = self._paperized_pixmap or self._original_pixmap
        if not ref_pixmap or ref_pixmap.isNull():
            # Draw helpful placeholder banner
            painter.setPen(QColor(150, 150, 150))
            font = QFont("sans-serif", 13)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                self._placeholder_text,
            )
            return

        if self._view_mode == ViewMode.SIDE_BY_SIDE:
            self._paint_side_by_side(painter, ref_pixmap)
        else:
            self._paint_single_or_split(painter, ref_pixmap)

    def _paint_single_or_split(self, painter: QPainter, ref: QPixmap) -> None:
        page_rect = self._get_page_rect()

        # Draw Page Drop Shadow
        shadow_rect = page_rect.translated(4, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(shadow_rect, 4, 4)

        # Draw Base Page Border
        painter.setPen(QColor(100, 100, 100, 80))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(page_rect)

        orig_pix = self._original_pixmap or ref
        paper_pix = self._paperized_pixmap or ref

        if self._view_mode == ViewMode.ORIGINAL:
            painter.drawPixmap(page_rect.toRect(), orig_pix)
            self._draw_pill_badge(painter, page_rect.left() + 16, page_rect.top() + 16, "Original (White)")
            return

        if self._view_mode == ViewMode.PAPERIZED:
            painter.drawPixmap(page_rect.toRect(), paper_pix)
            self._draw_pill_badge(painter, page_rect.left() + 16, page_rect.top() + 16, "Paperized")
            return

        # ViewMode.SPLIT:
        div_x = self._get_divider_screen_x(page_rect)

        # 1. Left side (Original): clip to left of divider
        painter.save()
        clip_left = QRectF(page_rect.left(), page_rect.top(), div_x - page_rect.left(), page_rect.height())
        painter.setClipRect(clip_left)
        painter.drawPixmap(page_rect.toRect(), orig_pix)
        self._draw_pill_badge(painter, page_rect.left() + 16, page_rect.top() + 16, "Original")
        painter.restore()

        # 2. Right side (Paperized): clip to right of divider
        painter.save()
        clip_right = QRectF(div_x, page_rect.top(), page_rect.right() - div_x, page_rect.height())
        painter.setClipRect(clip_right)
        painter.drawPixmap(page_rect.toRect(), paper_pix)
        self._draw_pill_badge(painter, page_rect.right() - 95, page_rect.top() + 16, "Paperized")
        painter.restore()

        # 3. Draw Splitter Divider Line
        divider_pen = QPen(QColor(255, 255, 255, 230), 2.5)
        painter.setPen(divider_pen)
        painter.drawLine(QPointF(div_x, page_rect.top()), QPointF(div_x, page_rect.bottom()))

        # 4. Draw Grip Handle Circle
        handle_y = page_rect.center().y()
        handle_radius = 16.0
        painter.setPen(QPen(QColor(30, 30, 30, 180), 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawEllipse(QPointF(div_x, handle_y), handle_radius, handle_radius)

        # Handle arrows '< | >'
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.drawLine(QPointF(div_x - 5, handle_y - 4), QPointF(div_x - 8, handle_y))
        painter.drawLine(QPointF(div_x - 8, handle_y), QPointF(div_x - 5, handle_y + 4))

        painter.drawLine(QPointF(div_x + 5, handle_y - 4), QPointF(div_x + 8, handle_y))
        painter.drawLine(QPointF(div_x + 8, handle_y), QPointF(div_x + 5, handle_y + 4))

    def _paint_side_by_side(self, painter: QPainter, ref: QPixmap) -> None:
        target_w = ref.width() * self._zoom
        target_h = ref.height() * self._zoom
        spacing = 24.0

        total_w = target_w * 2 + spacing
        start_x = (self.width() - total_w) / 2.0 + self._pan_offset.x()
        start_y = (self.height() - target_h) / 2.0 + self._pan_offset.y()

        left_rect = QRectF(start_x, start_y, target_w, target_h)
        right_rect = QRectF(start_x + target_w + spacing, start_y, target_w, target_h)

        # Shadows
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 45))
        painter.drawRoundedRect(left_rect.translated(4, 6), 4, 4)
        painter.drawRoundedRect(right_rect.translated(4, 6), 4, 4)

        orig_pix = self._original_pixmap or ref
        paper_pix = self._paperized_pixmap or ref

        painter.drawPixmap(left_rect.toRect(), orig_pix)
        painter.drawPixmap(right_rect.toRect(), paper_pix)

        self._draw_pill_badge(painter, left_rect.left() + 14, left_rect.top() + 14, "Original (White)")
        self._draw_pill_badge(painter, right_rect.left() + 14, right_rect.top() + 14, "Paperized")

    def _draw_pill_badge(self, painter: QPainter, x: float, y: float, text: str) -> None:
        """Draw an elegant translucent badge over the page."""
        font = QFont("sans-serif", 9)
        font.setBold(True)
        painter.setFont(font)

        padding_x = 10
        padding_y = 5
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(text)
        text_h = metrics.height()

        pill_rect = QRectF(x, y, text_w + padding_x * 2, text_h + padding_y * 2)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 20, 20, 180))
        painter.drawRoundedRect(pill_rect, 10, 10)

        painter.setPen(QColor(245, 245, 245))
        painter.drawText(
            pill_rect,
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

    # Mouse & Interactive Split Dragging Events
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            page_rect = self._get_page_rect()
            if self._view_mode == ViewMode.SPLIT and not page_rect.isEmpty():
                div_x = self._get_divider_screen_x(page_rect)
                # Check if click is near divider line (within 20px)
                if abs(event.position().x() - div_x) <= 22:
                    self._is_dragging_divider = True
                    self.setCursor(Qt.CursorShape.SplitHCursor)
                    return
                # Clicking anywhere inside page moves divider immediately
                elif page_rect.contains(event.position()):
                    self._is_dragging_divider = True
                    self._update_split_from_pos(event.position().x(), page_rect)
                    self.setCursor(Qt.CursorShape.SplitHCursor)
                    return

            # Otherwise initiate canvas pan
            self._is_panning = True
            self._pan_start_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        elif event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        page_rect = self._get_page_rect()

        if self._is_dragging_divider and not page_rect.isEmpty():
            self._update_split_from_pos(event.position().x(), page_rect)
            return

        if self._is_panning:
            delta = event.position() - self._pan_start_pos
            self._pan_start_pos = event.position()
            self._pan_offset += delta
            self.update()
            return

        # Cursor hover detection
        if self._view_mode == ViewMode.SPLIT and not page_rect.isEmpty():
            div_x = self._get_divider_screen_x(page_rect)
            if abs(event.position().x() - div_x) <= 15:
                self.setCursor(Qt.CursorShape.SplitHCursor)
                return

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._is_dragging_divider = False
        self._is_panning = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _update_split_from_pos(self, mouse_x: float, page_rect: QRectF) -> None:
        fraction = (mouse_x - page_rect.left()) / page_rect.width()
        self._split_fraction = max(0.02, min(fraction, 0.98))
        self.dividerMoved.emit(self._split_fraction)
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom with Ctrl+Wheel, or pan vertically with standard wheel."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            delta_y = event.angleDelta().y() / 4.0
            self._pan_offset += QPointF(0, delta_y)
            self.update()
            event.accept()
