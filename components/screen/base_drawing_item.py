from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
)
from components.screen.transform_handler import TransformHandler


class BaseDrawingItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        # Enable selecting, moving and geometry-change notifications
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        # Create a transform handler for resize/rotate handles
        self.transform_handler = TransformHandler(self)

        self._is_hovering = False
        self._is_transforming = False
        self._active_handle = None
        self._is_moving = False

        # Dictionary to store arbitrary properties
        self.properties = {}

    def boundingRect(self) -> QRectF:
        """Return the item’s bounding rectangle (override in subclasses)."""
        raise NotImplementedError

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the item and, if selected, its transform handles."""
        self._paint_content(painter, option, widget)

        # Only draw transform handles when selected and not during a move
        if self.isSelected():
            self.transform_handler.paint(painter, option, widget)
        elif self._is_hovering:
            self._paint_hover(painter)

    def _paint_content(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Subclasses should implement actual content drawing here."""
        raise NotImplementedError

    def _paint_hover(self, painter: QPainter) -> None:
        """Draw a dashed rectangle on hover when not selected."""
        rect = self.boundingRect()
        painter.setPen(QPen(QColor("#888888"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle press: start transform on handle or start move."""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.isSelected()
        ):
            pos = event.pos()
            handle = self.transform_handler.handle_at(pos)
            if handle is not None:
                self._is_transforming = True
                self._active_handle = handle
                self.transform_handler.start_transform_at(handle, pos)
                event.accept()
                return

        # When starting a move via mouse press, mark `_is_moving`
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_moving = True
            # Invalidate transform cache so handles disappear while moving
            self.transform_handler.invalidate_cache()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle move or transform updates."""
        if self._is_transforming and self._active_handle is not None:
            self.transform_handler.update_transform(event.pos())
            event.accept()
            return

        # Normal movement is handled by QGraphicsItem; keep tracking
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._is_moving = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """End move or transform on release."""
        if (
            self._is_transforming
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._is_transforming = False
            self._active_handle = None
            self.transform_handler.end_transform()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton and self._is_moving:
            self._is_moving = False
            # Recalculate handles and repaint
            self.transform_handler.invalidate_cache()
            self.update()
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Track hover state to draw outline."""
        self._is_hovering = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Change cursor based on handle under mouse when selected."""
        if self.isSelected():
            handle = self.transform_handler.handle_at(event.pos())
            if handle is not None:
                cursor = self.transform_handler.cursor_for_handle(handle)
                self.setCursor(cursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Reset hover state and cursor."""
        self._is_hovering = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """Respond to selection and position changes."""
        if (
            change
            == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
        ):
            # Skip drawing handles while moving; cache invalidated on release
            self.transform_handler.invalidate_cache()
        elif (
            change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange
        ):
            # Force a repaint so handles appear/disappear immediately
            self.update()
        return super().itemChange(change, value)

    def update_properties(self, props):
        """Update this item's properties dictionary and refresh handles."""
        for k, v in props.items():
            self.properties[k] = v
        self.transform_handler.invalidate_cache()
        self.update()
