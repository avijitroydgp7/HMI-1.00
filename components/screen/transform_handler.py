from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
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
        self.start_aspect_ratio = None

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
        painter.setPen(
            QPen(
                self.HANDLE_COLOR,
                1,
                Qt.PenStyle.DashLine,
            )
        )
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
        if self.start_rect.height() != 0:
            self.start_aspect_ratio = (
                self.start_rect.width() / self.start_rect.height()
            )
        else:
            self.start_aspect_ratio = None
    def update_transform(
        self,
        pos: QPointF,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ):
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

            new_angle = self.parent_item.rotation() + angle_delta
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                new_angle = round(new_angle / 15.0) * 15.0

            self.parent_item.setTransformOriginPoint(
                center
            )
            self.parent_item.setRotation(new_angle)
            # Update start_pos so we can rotate smoothly on the next move
            self.start_pos = QPointF(pos)
            return True

        # Constrain aspect ratio when shift is held
        if (
            modifiers & Qt.KeyboardModifier.ShiftModifier
            and self.start_aspect_ratio
        ):
            ratio = self.start_aspect_ratio
            if self.active_handle in (
                self.TOP_LEFT,
                self.TOP_RIGHT,
                self.BOTTOM_LEFT,
                self.BOTTOM_RIGHT,
            ):
                width = rect.width()
                height = rect.height()
                if abs(dx) > abs(dy):
                    height = width / ratio
                    if self.active_handle in (
                        self.TOP_LEFT,
                        self.TOP_RIGHT,
                    ):
                        rect.setTop(rect.bottom() - height)
                    else:
                        rect.setBottom(rect.top() + height)
                else:
                    width = height * ratio
                    if self.active_handle in (
                        self.TOP_LEFT,
                        self.BOTTOM_LEFT,
                    ):
                        rect.setLeft(rect.right() - width)
                    else:
                        rect.setRight(rect.left() + width)
            elif self.active_handle in (
                self.LEFT,
                self.RIGHT,
            ):
                width = rect.width()
                height = width / ratio
                center_y = rect.center().y()
                rect.setTop(center_y - height / 2)
                rect.setBottom(center_y + height / 2)
            elif self.active_handle in (
                self.TOP,
                self.BOTTOM,
            ):
                height = rect.height()
                width = height * ratio
                center_x = rect.center().x()
                rect.setLeft(center_x - width / 2)
                rect.setRight(center_x + width / 2)


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
        self.parent_item.update()
        return True

    def end_transform(self):
        """Reset transform state and invalidate cached handles."""
        self.active_handle = None
        self.start_rect = None
        self.start_pos = None
        self.start_transform = None
        self.invalidate_cache()

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
