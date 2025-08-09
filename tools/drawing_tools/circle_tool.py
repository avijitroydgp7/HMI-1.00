from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from components.screen.base_drawing_item import BaseDrawingItem

class CircleTool(BaseDrawingItem):
    """
    Circle drawing tool with transform capabilities.
    """
    
    def __init__(self, x, y, diameter=60, color="#5a6270"):
        super().__init__()
        self.setPos(x, y)
        self.properties = {
            "diameter": diameter,
            "color": color,
            "border_color": "#222222",
            "border_width": 2
        }
    
    def boundingRect(self):
        """
        Return the bounding rectangle of the circle.
        """
        return QRectF(0, 0, self.properties["diameter"], self.properties["diameter"])
    
    def _paint_content(self, painter, option, widget=None):
        """
        Paint the circle.
        """
        # Set up brush and pen
        brush = QBrush(QColor(self.properties["color"]))
        pen = QPen(QColor(self.properties["border_color"]), self.properties["border_width"])
        
        # Draw the circle
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawEllipse(self.boundingRect())
    
    def update_properties(self, props):
        """
        Update circle properties.
        """
        super().update_properties(props)
        self.prepareGeometryChange()
        self.update()