"""
Base class for draggable graphics items with selection support.
"""

from typing import Optional
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
)


class DraggableGraphicsItem(QGraphicsItem):
    """Base class for draggable graphics items."""

    def __init__(self, element_data, parent=None):
        super().__init__(parent)
        self.element_data = element_data
        self._is_hovering = False

        # Enable selection, movement, focus and geometry change notifications
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle for painting and selection."""
        return QRectF(
            0,
            0,
            self.element_data.size["width"],
            self.element_data.size["height"],
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ):
        """Paint the item and selection/hover outlines."""
        self._paint_content(painter, option, widget)

        # Draw selection overlay if selected
        if self.isSelected():
            self._paint_selection(painter)

        # Draw hover outline when not selected
        if self._is_hovering and not self.isSelected():
            self._paint_hover(painter)

    def _paint_content(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget],
    ):
        """Subclasses must implement this to draw the actual item."""
        raise NotImplementedError

    def _paint_selection(self, painter: QPainter):
        """Override to paint selection handles/decoration."""
        pass

    def _paint_hover(self, painter: QPainter):
        """Draw a dashed rectangle on hover when unselected."""
        rect = self.boundingRect()
        painter.setPen(QPen(QColor("#888888"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Begin hover tracking and request repaint."""
        self._is_hovering = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """End hover tracking and request repaint."""
        self._is_hovering = False
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """Repaint on selection changes; override for custom behavior."""
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange
        ):
            self.update()
        elif (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
        ):
            # Placeholder for undo/redo support
            pass
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Change cursor on press and forward to base implementation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Restore cursor on release and forward to base implementation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(
        self, event: QGraphicsSceneMouseEvent
    ) -> None:
        """Base double-click behavior (can be overridden)."""
        super().mouseDoubleClickEvent(event)
