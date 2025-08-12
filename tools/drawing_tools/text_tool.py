from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QColor, QFontMetrics
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from components.screen.base_drawing_item import BaseDrawingItem

class TextTool(BaseDrawingItem):
    """
    Text drawing tool with transform capabilities.
    """
    
    def __init__(self, x, y, text="Text", font_size=14, color="#222222", font_family="Arial"):
        super().__init__()
        self.setPos(x, y)
        self.properties = {
            "text": text,
            "font_size": font_size,
            "color": color,
            "font_family": font_family,
            "bold": False,
            "italic": False,
            "alignment": Qt.AlignmentFlag.AlignLeft
        }
        self._text_rect = self._calculate_text_rect()
    
    def _calculate_text_rect(self):
        """
        Calculate the bounding rectangle of the text.
        """
        font = self._create_font()
        metrics = QFontMetrics(font)
        text = self.properties["text"]
        
        # Calculate text width and height
        width = metrics.horizontalAdvance(text)
        height = metrics.height()
        
        # Add some padding
        padding = 5
        return QRectF(0, 0, width + padding * 2, height + padding * 2)
    
    def _create_font(self):
        """
        Create a font based on the current properties.
        """
        font = QFont(self.properties["font_family"], self.properties["font_size"])
        font.setBold(self.properties.get("bold", False))
        font.setItalic(self.properties.get("italic", False))
        return font
    
    def contentRect(self):
        """Return the rectangle occupied by the text content."""
        return self._text_rect
    
    def _paint_content(self, painter, option, widget=None):
        """
        Paint the text.
        """
        # Set up font and color
        painter.setFont(self._create_font())
        painter.setPen(QColor(self.properties["color"]))
        
        # Draw the text
        rect = self.contentRect()
        padding = 5
        text_rect = rect.adjusted(padding, padding, -padding, -padding)
        painter.drawText(text_rect, self.properties.get("alignment", Qt.AlignmentFlag.AlignLeft), self.properties["text"])
    
    def update_properties(self, props):
        """
        Update text properties.
        """
        super().update_properties(props)

        # Recalculate text rectangle if text or font properties change
        if any(
            key in props
            for key in ["text", "font_size", "font_family", "bold", "italic"]
        ):
            self.prepareGeometryChange()
            self._text_rect = self._calculate_text_rect()
            self.update()
