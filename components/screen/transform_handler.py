from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QGuiApplication
from PyQt6.QtWidgets import QGraphicsItem
import math


class TransformHandler:
    """
    Provides resize and rotate handles around an item and applies
    size/rotation changes based on mouse interaction.
    """

    # Enumeration of handle positions
    TOP_LEFT = 0
    TOP = 1
    TOP_RIGHT = 2
    RIGHT = 3
    BOTTOM_RIGHT = 4
    BOTTOM = 5
    BOTTOM_LEFT = 6
    LEFT = 7
    ROTATION = 8

    # Colors for handles and borders
    HANDLE_COLOR = QColor(0, 120, 215)
    HANDLE_BORDER_COLOR = QColor(255, 255, 255)
    ROTATION_HANDLE_COLOR = QColor(0, 200, 0)

    def __init__(self, parent_item: QGraphicsItem):
        self.parent_item = parent_item
        self.handle_size = 8.0
        self.handle_space = 1.0
        self.rotation_offset = 20.0

        self.handles = {}
        self._handles_cache = None
        self._last_rect = None

        # State for ongoing transform
        self.active_handle = None
        self.start_rect = None
        self.start_pos = None
        self.start_transform = None

        # preview state for dashed transform line
        self._preview_active = False

    def update_handles(self):
        """Recompute handle rectangles if necessary."""
        rect = self.parent_item.boundingRect()
        if (
            self._handles_cache is not None
            and self._last_rect == rect
        ):
            self.handles = self._handles_cache
            return

        self._last_rect = QRectF(rect)
        hs = self.handle_size
        sp = self.handle_space

        self.handles = {
            self.TOP_LEFT: QRectF(
                rect.left() - hs - sp,
                rect.top() - hs - sp,
                hs,
                hs,
            ),
            self.TOP: QRectF(
                rect.center().x() - hs / 2.0,
                rect.top() - hs - sp,
                hs,
                hs,
            ),
            self.TOP_RIGHT: QRectF(
                rect.right() + sp,
                rect.top() - hs - sp,
                hs,
                hs,
            ),
            self.RIGHT: QRectF(
                rect.right() + sp,
                rect.center().y() - hs / 2.0,
                hs,
                hs,
            ),
            self.BOTTOM_RIGHT: QRectF(
                rect.right() + sp,
                rect.bottom() + sp,
                hs,
                hs,
            ),
            self.BOTTOM: QRectF(
                rect.center().x() - hs / 2.0,
                rect.bottom() + sp,
                hs,
                hs,
            ),
            self.BOTTOM_LEFT: QRectF(
                rect.left() - hs - sp,
                rect.bottom() + sp,
                hs,
                hs,
            ),
            self.LEFT: QRectF(
                rect.left() - hs - sp,
                rect.center().y() - hs / 2.0,
                hs,
                hs,
            ),
            self.ROTATION: QRectF(
                rect.center().x() - hs / 2.0,
                rect.top() - self.rotation_offset - hs,
                hs,
                hs,
            ),
        }
        # Cache a shallow copy of the handles dictionary
        self._handles_cache = dict(self.handles)

    def paint(self, painter: QPainter, option=None, widget=None):
        """Draw selection outline, rotation connector, and handles."""
        # Skip drawing handles while parent item is being dragged
        if getattr(self.parent_item, "_is_moving", False):
            return

        self.update_handles()
        rect = self.parent_item.boundingRect()

        # Draw dashed selection outline
        painter.setPen(QPen(self.HANDLE_COLOR, 1,
                Qt.PenStyle.DashLine if self._preview_active else Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        # Draw the connector line for rotation
        painter.setPen(
            QPen(
                self.ROTATION_HANDLE_COLOR,
                1,
                Qt.PenStyle.SolidLine,
            )
        )
        top_center = self.handles[self.TOP].center()
        rot_center = self.handles[self.ROTATION].center()
        painter.drawLine(top_center, rot_center)

        # Draw each handle
        for hid, hrect in self.handles.items():
            if hid == self.ROTATION:
                painter.setBrush(
                    QBrush(self.ROTATION_HANDLE_COLOR)
                )
                painter.setPen(
                    QPen(
                        self.HANDLE_BORDER_COLOR, 1
                    )
                )
            else:
                painter.setBrush(QBrush(self.HANDLE_COLOR))
                painter.setPen(
                    QPen(
                        self.HANDLE_BORDER_COLOR, 1
                    )
                )
            painter.drawRect(hrect)

    def handle_at(self, pos: QPointF):
        """Return the handle ID at the given local position, if any."""
        self.update_handles()
        for hid, hrect in self.handles.items():
            if hrect.contains(pos):
                return hid
        return None

    def cursor_for_handle(self, handle_id):
        """Return the appropriate cursor for a given handle ID."""
        if handle_id in (
            self.TOP_LEFT,
            self.BOTTOM_RIGHT,
        ):
            return Qt.CursorShape.SizeFDiagCursor
        if handle_id in (
            self.TOP_RIGHT,
            self.BOTTOM_LEFT,
        ):
            return Qt.CursorShape.SizeBDiagCursor
        if handle_id in (self.TOP, self.BOTTOM):
            return Qt.CursorShape.SizeVerCursor
        if handle_id in (self.LEFT, self.RIGHT):
            return Qt.CursorShape.SizeHorCursor
        if handle_id == self.ROTATION:
            return Qt.CursorShape.CrossCursor
        return Qt.CursorShape.ArrowCursor

    def start_transform_at(
        self, handle_id, pos: QPointF
    ):
        """Store initial geometry and position for transformations."""
        self.active_handle = handle_id
        self.start_rect = QRectF(
            self.parent_item.boundingRect()
        )
        self.start_pos = QPointF(pos)
        self.start_transform = (
            self.parent_item.transform()
        )

    def update_transform(self, pos: QPointF):
        """Apply resizing or rotation based on mouse movement."""
        if self.active_handle is None:
            return False

        dx = pos.x() - self.start_pos.x()
        dy = pos.y() - self.start_pos.y()

        rect = QRectF(self.start_rect)

        # Resize logic
        if self.active_handle == self.TOP_LEFT:
            rect.setTopLeft(
                rect.topLeft() + QPointF(dx, dy)
            )
        elif self.active_handle == self.TOP:
            rect.setTop(rect.top() + dy)
        elif self.active_handle == self.TOP_RIGHT:
            rect.setTopRight(
                rect.topRight() + QPointF(dx, dy)
            )
        elif self.active_handle == self.RIGHT:
            rect.setRight(rect.right() + dx)
        elif self.active_handle == self.BOTTOM_RIGHT:
            rect.setBottomRight(
                rect.bottomRight() + QPointF(dx, dy)
            )
        elif self.active_handle == self.BOTTOM:
            rect.setBottom(rect.bottom() + dy)
        elif self.active_handle == self.BOTTOM_LEFT:
            rect.setBottomLeft(
                rect.bottomLeft() + QPointF(dx, dy)
            )

        # Maintain aspect ratio if Shift is pressed
        if bool(QGuiApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier) and self.active_handle != self.ROTATION:
            ow = max(1e-6, self.start_rect.width())
            oh = max(1e-6, self.start_rect.height())
            aspect = ow / oh
            r = rect.normalized()
            w, h = r.width(), r.height()
            if w / h > aspect:
                w = h * aspect
            else:
                h = w / aspect
            # Anchor to the opposite corner from the dragged handle
            if self.active_handle in (self.TOP_LEFT, self.TOP, self.LEFT):
                anchor = QPointF(self.start_rect.right(), self.start_rect.bottom())
                rect = QRectF(anchor.x() - w, anchor.y() - h, w, h)
            elif self.active_handle in (self.TOP_RIGHT, self.TOP, self.RIGHT):
                anchor = QPointF(self.start_rect.left(), self.start_rect.bottom())
                rect = QRectF(anchor.x(), anchor.y() - h, w, h)
            elif self.active_handle in (self.BOTTOM_LEFT, self.BOTTOM, self.LEFT):
                anchor = QPointF(self.start_rect.right(), self.start_rect.top())
                rect = QRectF(anchor.x() - w, anchor.y(), w, h)
            else:  # BOTTOM_RIGHT and others
                anchor = QPointF(self.start_rect.left(), self.start_rect.top())
                rect = QRectF(anchor.x(), anchor.y(), w, h)
        elif self.active_handle == self.LEFT:
            rect.setLeft(rect.left() + dx)
        elif self.active_handle == self.ROTATION:
            # Rotate around the local center
            center = (
                self.parent_item.boundingRect().center()
            )
            start_vec = self.start_pos - center
            curr_vec = pos - center
            start_angle = self._vector_angle(start_vec)
            curr_angle = self._vector_angle(curr_vec)
            angle_delta = curr_angle - start_angle

            self.parent_item.setTransformOriginPoint(
                center
            )
            self.parent_item.setRotation(
                self.parent_item.rotation()
                + angle_delta
            )
            # Update start_pos so we can rotate smoothly on the next move
            self.start_pos = QPointF(pos)
            return True

        # Enforce a minimum size
        min_size = 8.0
        if rect.width() < min_size:
            if self.active_handle in (
                self.TOP_LEFT,
                self.BOTTOM_LEFT,
                self.LEFT,
            ):
                rect.setLeft(rect.right() - min_size)
            else:
                rect.setRight(rect.left() + min_size)
        if rect.height() < min_size:
            if self.active_handle in (
                self.TOP_LEFT,
                self.TOP,
                self.TOP_RIGHT,
            ):
                rect.setTop(rect.bottom() - min_size)
            else:
                rect.setBottom(rect.top() + min_size)

        # Apply updated geometry using available API
        if hasattr(self.parent_item, "setRect"):
            try:
                self.parent_item.setRect(rect)
            except Exception:
                pass
        elif hasattr(self.parent_item, "resize"):
            try:
                self.parent_item.resize(
                    rect.width(), rect.height()
                )
            except Exception:
                pass

        # Update associated properties dict if present
        if (
            hasattr(self.parent_item, "properties")
            and isinstance(
                self.parent_item.properties, dict
            )
        ):
            self.parent_item.properties["width"] = (
                rect.width()
            )
            self.parent_item.properties["height"] = (
                rect.height()
            )
            if "x" in self.parent_item.properties:
                self.parent_item.properties["x"] = (
                    rect.x()
                )
            if "y" in self.parent_item.properties:
                self.parent_item.properties["y"] = (
                    rect.y()
                )

        # Invalidate cached handles and request repaint
        self.invalidate_cache()
        self._preview_active = False
        self.parent_item.update()
        return True

    def end_transform(self):
        """Reset transform state and invalidate cached handles."""
        self.active_handle = None
        self.start_rect = None
        self.start_pos = None
        self.start_transform = None

        # preview state for dashed transform line
        self._preview_active = False
        self.invalidate_cache()
        self._preview_active = False

    def _vector_angle(self, vector: QPointF):
        """Compute the angle (in degrees) of a 2D vector."""
        if vector.x() == 0 and vector.y() == 0:
            return 0.0
        return math.degrees(
            math.atan2(vector.y(), vector.x())
        )

    def invalidate_cache(self):
        """Clear cached handle positions so they will be recomputed."""
        self._handles_cache = None
        self._last_rect = None
