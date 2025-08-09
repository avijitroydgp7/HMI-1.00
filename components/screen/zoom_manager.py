"""
ZoomManager - Advanced zoom functionality for screen widgets.
"""

from PyQt6.QtCore import QPointF, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QGraphicsView


class ZoomManager(QObject):
    """Manages advanced zoom functionality with smooth transitions."""

    zoom_changed = pyqtSignal(float)

    def __init__(self, graphics_view, parent=None):
        super().__init__(parent)
        self.graphics_view = graphics_view
        self._scale_factor = 1.0
        self._min_scale = 0.1
        self._max_scale = 10.0
        self._zoom_step = 1.2

        # We do not use an animation; zoom is applied immediately
        self.zoom_animation = None

    @property
    def scale_factor(self):
        return self._scale_factor

    def zoom_in(self, center=None, smooth=True):
        """Zoom in, optionally around a given scene point."""
        new_scale = min(
            self._scale_factor * self._zoom_step,
            self._max_scale,
        )
        self.set_scale(new_scale, center, smooth)

    def zoom_out(self, center=None, smooth=True):
        """Zoom out, optionally around a given scene point."""
        new_scale = max(
            self._scale_factor / self._zoom_step,
            self._min_scale,
        )
        self.set_scale(new_scale, center, smooth)

    def zoom_to_fit(self):
        """Zoom to fit the entire scene into the view."""
        if hasattr(self.graphics_view, "scene"):
            scene_rect = (
                self.graphics_view.scene().sceneRect()
            )
            view_rect = self.graphics_view.viewport().rect()
            scale_x = view_rect.width() / scene_rect.width()
            scale_y = view_rect.height() / scene_rect.height()
            new_scale = min(scale_x, scale_y) * 0.9
            self.set_scale(new_scale, smooth=True)

    def zoom_to_100(self):
        """Reset zoom to 100% (1.0 scale)."""
        self.set_scale(1.0, smooth=True)

    def set_scale(
        self, new_scale, center=None, smooth=True
    ):
        """Set the view scale directly, clamped to min/max."""
        target_scale = max(
            self._min_scale,
            min(new_scale, self._max_scale),
        )
        self._apply_scale(target_scale, center)

    def _apply_scale(self, scale, center=None):
        """Apply the target scale immediately, preserving center."""
        if center is None:
            center = self.graphics_view.mapToScene(
                self.graphics_view.viewport().rect().center()
            )

        # Save the current view center
        old_center = self.graphics_view.mapToScene(
            self.graphics_view.viewport().rect().center()
        )

        # Apply the new transform
        self.graphics_view.resetTransform()
        self.graphics_view.scale(scale, scale)

        # Translate to keep the apparent center constant
        if center:
            new_center = self.graphics_view.mapToScene(
                self.graphics_view.viewport().rect().center()
            )
            delta = new_center - old_center
            self.graphics_view.translate(
                delta.x(), delta.y()
            )

        self._scale_factor = scale
        self.zoom_changed.emit(self._scale_factor)

    def handle_wheel_event(
        self, event: QWheelEvent, modifiers=None
    ):
        """Intercept Ctrl+wheel to zoom, returning True if handled."""
        if modifiers is None:
            modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            pos = self.graphics_view.mapToScene(
                event.position().toPoint()
            )
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in(pos)
            else:
                self.zoom_out(pos)
            event.accept()
            return True
        return False

    def get_zoom_percentage(self) -> str:
        """
        Return a human‑friendly zoom percentage string.

        For example, a scale factor of 1.25 yields "125%".
        """
        return f"{int(round(self._scale_factor * 100))}%"
