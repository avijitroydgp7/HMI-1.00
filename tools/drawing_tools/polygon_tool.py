from PyQt6.QtCore import QRectF, QPointF
from PyQt6.QtGui import QBrush, QPen, QColor, QPolygonF
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from components.screen.base_drawing_item import BaseDrawingItem

class PolygonTool(BaseDrawingItem):
    """
    Polygon drawing tool with transform capabilities.
    """
    
    def __init__(self, points, color="#5a6270"):
        super().__init__()
        # Calculate the bounding box of the points to set position
        x_values = [p[0] for p in points]
        y_values = [p[1] for p in points]
        min_x, min_y = min(x_values), min(y_values)
        
        # Set position to the top-left corner of the bounding box
        self.setPos(min_x, min_y)
        
        # Adjust points to be relative to the top-left corner
        relative_points = [(x - min_x, y - min_y) for x, y in points]
        
        self.properties = {
            "points": relative_points,
            "color": color,
            "border_color": "#222222",
            "border_width": 2
        }
    
    def contentRect(self):
        """Return the rectangle occupied by the polygon's content."""
        points = self.properties["points"]
        if not points:
            return QRectF(0, 0, 0, 0)

        x_values = [p[0] for p in points]
        y_values = [p[1] for p in points]
        
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def _paint_content(self, painter, option, widget=None):
        """
        Paint the polygon.
        """
        # Create polygon from points
        polygon = QPolygonF([QPointF(x, y) for x, y in self.properties["points"]])
        
        # Set up brush and pen
        brush = QBrush(QColor(self.properties["color"]))
        pen = QPen(QColor(self.properties["border_color"]), self.properties["border_width"])
        
        # Draw the polygon
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawPolygon(polygon)
    
    def update_properties(self, props):
        """
        Update polygon properties.
        """
        if "points" in props:
            # If points are updated, we need to recalculate the position
            old_points = self.properties["points"]
            new_points = props["points"]
            
            # If the points are in absolute coordinates, convert to relative
            if len(new_points) > 0 and isinstance(new_points[0], (list, tuple)) and len(new_points[0]) == 2:
                x_values = [p[0] for p in new_points]
                y_values = [p[1] for p in new_points]
                min_x, min_y = min(x_values), min(y_values)
                
                # Update position
                self.setPos(min_x, min_y)
                
                # Convert to relative points
                props["points"] = [(x - min_x, y - min_y) for x, y in new_points]
        
        super().update_properties(props)
