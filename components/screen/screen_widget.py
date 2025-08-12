#component/screen/screen_widget
from __future__ import annotations

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsRectItem, QGraphicsTextItem, QFrame, QGraphicsItem,
    QGraphicsSceneMouseEvent
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QObject
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QMouseEvent, QWheelEvent, QKeyEvent
)

from services.screen_data_service import screen_service
from services.settings_service import settings_service
from utils import constants

from tools.drawing_tools.rectangle_tool import RectangleTool
from tools.drawing_tools.circle_tool import CircleTool
from tools.drawing_tools.polygon_tool import PolygonTool
from tools.drawing_tools.text_tool import TextTool


@dataclass
class ElementData:
    """Data structure for screen elements."""
    element_id: str
    element_type: str
    position: Dict[str, int]
    size: Dict[str, int]
    properties: Dict[str, Any]


class ScreenElement(ABC):
    """Abstract base class for screen elements."""
    
    def __init__(self, data: ElementData):
        self.data = data
    
    @abstractmethod
    def create_graphics_item(self) -> QGraphicsItem:
        """Create the QGraphicsItem for this element."""
        pass
    
    @abstractmethod
    def update_properties(self, properties: Dict[str, Any]) -> None:
        """Update element properties."""
        pass


LOD_THRESHOLD = 0.5  # Zoom level to switch between simple and detailed rendering


from components.screen.base_drawing_item import BaseDrawingItem

class ButtonGraphicsItem(BaseDrawingItem):
    """A custom graphics item for a button with Level of Detail (LOD) support and transform capabilities."""

    def __init__(self, data: ElementData):
        super().__init__()
        self.element_data = data
        self.setPos(self.element_data.position['x'], self.element_data.position['y'])
        
        # Set properties for transform handler
        self.properties = {
            'width': self.element_data.size['width'],
            'height': self.element_data.size['height'],
            **self.element_data.properties
        }

    def contentRect(self) -> QRectF:
        """Return the rectangle occupied by the button content."""
        return QRectF(
            0,
            0,
            self.element_data.size['width'],
            self.element_data.size['height'],
        )

    def _paint_content(self, painter: QPainter, option, widget=None) -> None:
        """Paint the button with LOD."""
        lod = painter.worldTransform().m11()

        bg_color = QColor(self.element_data.properties.get('background_color', '#5a6270'))
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRect(self.contentRect())

        if lod > LOD_THRESHOLD:
            text_color = QColor(self.element_data.properties.get('text_color', '#ffffff'))
            painter.setPen(QPen(text_color))
            
            font = QFont("Arial", 10)
            painter.setFont(font)
            
            label = self.element_data.properties.get('label', 'Button')
            painter.drawText(
                self.contentRect(),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )
            
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle double-click to open button properties dialog."""
        from components.button.button_properties_dialog import ButtonPropertiesDialog
        
        # Get the scene and view
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            
            # Open the properties dialog with the view as parent
            dialog = ButtonPropertiesDialog(self.element_data.properties, view)
            
            # Store references to button item and canvas in the dialog
            dialog.button_item = self
            dialog.canvas = view
            
            if dialog.exec():
                # Update button properties if dialog was accepted
                updated_props = dialog.get_data()
                self.element_data.properties.update(updated_props)
                
                # Update transform handler properties
                self.update_properties(updated_props)
                
                # Notify the scene that the screen was modified
                if hasattr(view, 'screen_modified') and hasattr(view, 'screen_id'):
                    view.screen_modified.emit(view.screen_id)
        
        event.accept()
        
    def update_properties(self, props):
        """Update button properties."""
        if 'width' in props or 'height' in props:
            self.prepareGeometryChange()

        if 'width' in props:
            self.element_data.size['width'] = props['width']
        if 'height' in props:
            self.element_data.size['height'] = props['height']

        for k, v in props.items():
            self.element_data.properties[k] = v

        super().update_properties(props)         
        self.update()


class ButtonElement(ScreenElement):
    """Button element implementation."""
    
    def create_graphics_item(self) -> QGraphicsItem:
        """Create a button graphics item using the custom LOD-aware item."""
        return ButtonGraphicsItem(self.data)

    def update_properties(self, properties: Dict[str, Any]) -> None:
        """Update button properties."""
        self.data.properties.update(properties)


class ScreenWidget(QWidget):
    """
    Widget for displaying and editing a screen in the HMI Designer.
    """
    
    screen_modified = pyqtSignal(str)
    selection_changed = pyqtSignal(str, object)
    selection_dragged = pyqtSignal(object)
    mouse_moved_on_scene = pyqtSignal(object)
    mouse_left_scene = pyqtSignal()
    zoom_changed = pyqtSignal(str)
    open_screen_requested = pyqtSignal(str)
    
    def __init__(self, screen_id: str, parent: Optional[QWidget] = None) -> None:
        """Initialize the ScreenWidget."""
        super().__init__(parent)
        self.screen_id = screen_id
        self.screen_data: Optional[Dict[str, Any]] = None
        self.active_tool = constants.TOOL_SELECT
        self.placement_mode = False
        self.placement_tool = None
        self._scale_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._elements: List[ScreenElement] = []
        self._current_theme = 'dark_theme'
        
        self._setup_ui()
        self._connect_signals()
        self._load_initial_theme()
        self._load_screen_data()
    
    def _setup_ui(self) -> None:
        """Set up the user interface with improved structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create canvas
        self.canvas = ScreenCanvas(self.screen_id, self)
        self.canvas.screen_modified.connect(self.screen_modified)
        self.canvas.selection_changed.connect(self.selection_changed)
        self.canvas.selection_dragged.connect(self.selection_dragged)
        self.canvas.mouse_moved_on_scene.connect(self.mouse_moved_on_scene)
        self.canvas.mouse_left_scene.connect(self.mouse_left_scene)
        self.canvas.zoom_changed.connect(self.zoom_changed)
        self.canvas.open_screen_requested.connect(self.open_screen_requested)
        
        # For backward compatibility
        self.design_canvas = self.canvas
        
        layout.addWidget(self.canvas)
    
    def _connect_signals(self) -> None:
        """Connect to service signals."""
        screen_service.screen_modified.connect(self._on_screen_modified)
    
    def _load_initial_theme(self) -> None:
        """Load the initial theme."""
        current_theme = settings_service.get_value("appearance/theme", "dark_theme")
        if current_theme is None:
            current_theme = "dark_theme"
        self.update_theme_colors(str(current_theme))
        self._load_screen_data()
    
    def set_active_tool(self, tool_name: str) -> None:
        """Set the active tool."""
        self.active_tool = tool_name
        
        # Enable placement mode for button and drawing tools
        drawing_tools = [
            constants.TOOL_BUTTON, constants.TOOL_RECTANGLE, constants.TOOL_CIRCLE,
            constants.TOOL_POLYGON, constants.TOOL_TEXT
        ]
        if tool_name in drawing_tools:
            self.placement_mode = True
            self.placement_tool = tool_name
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.placement_mode = False
            self.placement_tool = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Removed call to self._clear_placement_preview() here

        self.canvas.set_active_tool(tool_name)
    
    def update_theme_colors(self, theme_name: str) -> None:
        """Update theme colors."""
        self._current_theme = theme_name
        self.canvas.update_theme_colors(theme_name)
    
    def get_screen_data(self) -> Optional[Dict[str, Any]]:
        """Get current screen data."""
        return self.screen_data
    
    def get_zoom_percentage(self) -> str:
        """Get zoom percentage."""
        return f"{int(self._scale_factor * 100)}%"
    
    def zoom_in(self) -> None:
        """Zoom in."""
        self._scale_factor = min(self._scale_factor * 1.2, 10.0)
        self.canvas.set_scale_factor(self._scale_factor)
        self.zoom_changed.emit(self.get_zoom_percentage())
    
    def zoom_out(self) -> None:
        """Zoom out."""
        self._scale_factor = max(self._scale_factor / 1.2, 0.1)
        self.canvas.set_scale_factor(self._scale_factor)
        self.zoom_changed.emit(self.get_zoom_percentage())
    
    def _on_screen_modified(self, modified_screen_id: str) -> None:
        """Handle screen modification."""
        if modified_screen_id == self.screen_id:
            self.screen_data = screen_service.get_screen(self.screen_id)
            self.canvas.update_screen_data(self.screen_data)
    
    def update_screen_data(self) -> None:
        """Update screen data."""
        self.screen_data = screen_service.get_screen(self.screen_id)
        self.canvas.update_screen_data(self.screen_data)

    def _load_screen_data(self) -> None:
        """Load the screen data initially and update the canvas."""
        self.screen_data = screen_service.get_screen(self.screen_id)
        self.canvas.update_screen_data(self.screen_data)

    def refresh_selection_status(self) -> None:
        """Refresh the selection status of the canvas."""
        # Emit selection changed signal with empty data
        # This maintains compatibility with the events system
        self.selection_changed.emit(self.screen_id, None)


class ScreenCanvas(QGraphicsView):
    """
    Canvas widget for drawing and editing screen content with improved performance.
    """
    
    screen_modified = pyqtSignal(str)
    selection_changed = pyqtSignal(str, object)
    selection_dragged = pyqtSignal(object)
    mouse_moved_on_scene = pyqtSignal(object)
    mouse_left_scene = pyqtSignal()
    zoom_changed = pyqtSignal(str)
    open_screen_requested = pyqtSignal(str)
    
    def __init__(self, screen_id: str, parent: Optional[QWidget] = None) -> None:
        """Initialize the ScreenCanvas."""
        super().__init__(parent)
        self.screen_id = screen_id
        self.screen_data: Optional[Dict[str, Any]] = None
        self.active_tool = constants.TOOL_SELECT
        self._scale_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._elements: List[ScreenElement] = []
        self._current_theme = 'dark_theme'
        self._background_item: Optional[QGraphicsRectItem] = None
        
        # Placement mode variables
        self.placement_mode = False
        self.placement_tool = None
        self.preview_item = None
        self.last_mouse_pos = QPointF(0, 0)
        
        self._setup_scene()
        # Selection and movement
        from .transform_handler import TransformHandler
        from .selection_manager import SelectionManager

        self.transform_handler = TransformHandler(self)
        self.selection_manager = SelectionManager(self._scene)
        self.selection_manager.selection_changed.connect(
            lambda ids: self.selection_changed.emit(
                self.screen_id,
                [{'instance_id': item_id} for item_id in ids]
            )
        )
        self.selection_manager.item_moved.connect(
            lambda item_id, old_pos, new_pos: self.selection_dragged.emit(
                {'item_id': item_id, 'old_pos': old_pos, 'new_pos': new_pos}
            )
        )

        # State for marquee (drag) selection
        self._marquee_origin = QPointF()
        self._marquee_rect_item: QGraphicsRectItem | None = None
        self._marquee_active = False
        self._configure_view()
        
        # Initialize zoom manager
        from .zoom_manager import ZoomManager
        self.zoom_manager = ZoomManager(self)
        self.zoom_manager.zoom_changed.connect(self._on_zoom_changed)
        
        # Ensure zoom manager syncs with our scale
        self.zoom_manager.set_scale(self._scale_factor)
    
    def _setup_scene(self) -> None:
        """Set up the graphics scene."""
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
    
    def _configure_view(self) -> None:
        """Configure the view for optimal performance and quality."""
        # Performance and Quality settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setOptimizationFlags(QGraphicsView.OptimizationFlag.DontSavePainterState)

        
        # User interaction
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("ScreenCanvas")

    

    def update_screen_data(self, screen_data: Optional[Dict[str, Any]]) -> None:
        """Update the canvas with new screen data."""
        self.screen_data = screen_data
        self._clear_scene()
        
        if screen_data:
            self._create_background()
            self._create_elements()
            self._update_scene_rect()
            
        # Force a complete repaint of the view
        if self.viewport():
            self.viewport().update()
        self.update()
    
    def set_active_tool(self, tool_name: str) -> None:
        """Set the active tool."""
        # Deactivate current tool if any
        self.active_tool = tool_name
        
        # Enable placement mode for button and drawing tools
        drawing_tools = [
            constants.TOOL_BUTTON, constants.TOOL_RECTANGLE, constants.TOOL_CIRCLE,
            constants.TOOL_POLYGON, constants.TOOL_TEXT
        ]
        if tool_name in drawing_tools:
            self.placement_mode = True
            self.placement_tool = tool_name
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.placement_mode = False
            self.placement_tool = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._clear_placement_preview()

            

    
    def set_scale_factor(self, scale_factor: float) -> None:
        """Set the scale factor."""
        self._scale_factor = scale_factor
        self.resetTransform()
        self.scale(self._scale_factor, self._scale_factor)
        # Ensure zoom manager stays in sync
        if hasattr(self, 'zoom_manager'):
            self.zoom_manager.set_scale(scale_factor, smooth=False)
    
    def update_theme_colors(self, theme_name: str) -> None:
        """Update theme colors."""
        self._current_theme = theme_name
        self._update_background_color()
    
    def _clear_scene(self) -> None:
        """Clear the scene."""
        self._scene.clear()
        self._background_item = None
        self._elements.clear()
        self._clear_placement_preview()
    
    def _create_background(self) -> None:
        """Create the background rectangle."""
        if not self.screen_data:
            return
            
        size = self.screen_data.get('size', {'width': 1920, 'height': 1080})
        width = size['width']
        height = size['height']
        
        style = self.screen_data.get('style', {})
        
        if not style.get('transparent', False):
            color_hex = style.get('color1', '#ffffff')
            background_color = QColor(color_hex)
            
            self._background_item = QGraphicsRectItem(0, 0, width, height)
            self._background_item.setBrush(QBrush(background_color))
            self._background_item.setPen(QPen(Qt.PenStyle.NoPen))
            self._scene.addItem(self._background_item)
    
    def _create_elements(self) -> None:
        """Create screen elements."""
        if not self.screen_data:
            return
            
        elements = self.screen_data.get('children', [])
        for element_data in elements:
            element = self._create_element(element_data)
            if element:
                self._elements.append(element)
                graphics_item = element.create_graphics_item()
                if graphics_item:
                    self._scene.addItem(graphics_item)
    
    def _create_element(self, element_data: Dict[str, Any]) -> Optional[ScreenElement]:
        """Create a screen element from data."""
        element_type = element_data.get('type', 'unknown')
        element_data_obj = ElementData(
            element_id=element_data.get('instance_id', ''),
            element_type=element_type,
            position=element_data.get('position', {'x': 0, 'y': 0}),
            size=element_data.get('size', {'width': 100, 'height': 40}),
            properties=element_data.get('properties', {})
        )
        
        # Create a custom ScreenElement implementation for each element type
        if element_type == 'button':
            return ButtonElement(element_data_obj)
        elif element_type in ['line', 'rectangle', 'circle', 'polygon', 'polyline', 'arc', 'sector', 'text', 'table', 'image', 'freehand']:
            # Create a generic element that uses the appropriate graphics item creator
            class GenericElement(ScreenElement):
                def __init__(self, data: ElementData):
                    super().__init__(data)
                    self.item: Optional[QGraphicsItem] = None

                def create_graphics_item(self) -> QGraphicsItem | None:
                    props = self.data.properties
                    pos = self.data.position
                    size = self.data.size
                    
                    if self.data.element_type == constants.TOOL_RECTANGLE:
                        self.item = RectangleTool(pos['x'], pos['y'], size['width'], size['height'], props.get('color', '#000000'))
                    elif self.data.element_type == constants.TOOL_CIRCLE:
                        self.item = CircleTool(pos['x'], pos['y'], props.get('diameter', 50), props.get('color', '#000000'))
                    elif self.data.element_type == constants.TOOL_POLYGON:
                        self.item = PolygonTool(props.get('points', []), props.get('color', '#000000'))
                        self.item.setPos(pos['x'], pos['y'])
                    elif self.data.element_type == constants.TOOL_TEXT:
                        self.item = TextTool(pos['x'], pos['y'], props.get('text', ' '), props.get('font_size', 12), props.get('color', '#000000'))
                    
                    if self.item:
                        # Use 0 for user role, as is common practice for instance IDs
                        self.item.setData(0, self.data.element_id)
                    
                    return self.item

                def update_properties(self, properties: Dict[str, Any]) -> None:
                    self.data.properties.update(properties)
                    if self.item and hasattr(self.item, 'update_properties'):
                        self.item.update_properties(self.data.properties)

            return GenericElement(element_data_obj)

        
        return None
    
    def _update_scene_rect(self) -> None:
        """Update the scene rectangle."""
        if self.screen_data:
            size = self.screen_data.get('size', {'width': 1920, 'height': 1080})
            self._scene.setSceneRect(0, 0, size['width'], size['height'])
    
    def _update_background_color(self) -> None:
        """Update background color based on theme."""
        if self._background_item:
            # This would use theme manager in real implementation
            pass
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        scene_pos = self.mapToScene(event.pos())
        
        if self.active_tool == constants.TOOL_SELECT:
            item = self.itemAt(event.pos())
            self.selection_manager.handle_mouse_press(event, item)

            if item and item.isSelected():
                self.selection_manager.start_move(scene_pos)
            else:
                if (
                    event.button() == Qt.MouseButton.LeftButton
                    and not item
                ):
                    # Begin marquee selection
                    self._marquee_origin = scene_pos
                    self._marquee_active = True
                    self._marquee_rect_item = QGraphicsRectItem()
                    self._marquee_rect_item.setRect(QRectF(scene_pos, scene_pos))
                    pen = QPen(
                        self.transform_handler.HANDLE_COLOR,
                        1,
                        Qt.PenStyle.DashLine,
                    )
                    self._marquee_rect_item.setPen(pen)
                    self._marquee_rect_item.setBrush(Qt.BrushStyle.NoBrush)
                    self._marquee_rect_item.setFlag(
                        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
                        False,
                    )
                    self._marquee_rect_item.setZValue(10_000)
                    self._scene.addItem(self._marquee_rect_item)
                    event.accept()

            return

        if self.placement_mode:
            if self.placement_tool == constants.TOOL_BUTTON:
                self._place_button(scene_pos)
            else:
                self._place_drawing_object(scene_pos)
            
            # After placing, revert to select tool by notifying parent widget
            parent = self.parent()
            if isinstance(parent, ScreenWidget):
                parent.set_active_tool(constants.TOOL_SELECT)
            return

            

            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events."""
        scene_pos = self.mapToScene(event.pos())

        if self.active_tool == constants.TOOL_SELECT:
            if self._marquee_active:
                rect = QRectF(self._marquee_origin, scene_pos).normalized()
                if self._marquee_rect_item:
                    self._marquee_rect_item.setRect(rect)
                event.accept()
                return
            if self.selection_manager._is_moving:
                self.selection_manager.update_move(scene_pos)
                return

        if self.placement_mode and self.placement_tool == constants.TOOL_BUTTON:
            self._update_placement_preview(scene_pos)
            return
            
        super().mouseMoveEvent(event)

    
    def _clear_placement_preview(self) -> None:
        """Clear the placement preview item."""
        try:
            if self.preview_item is not None:
                if hasattr(self.preview_item, 'scene') and self.preview_item.scene() is not None:
                    self._scene.removeItem(self.preview_item)
        except (RuntimeError, AttributeError):
            # Item has already been deleted or is invalid
            pass
        finally:
            self.preview_item = None

    def _update_placement_preview(self, scene_pos) -> None:
        """Update the preview item position."""
        if not self.preview_item:
            # Create a preview button with default size and properties
            default_data = ElementData(
                element_id="preview",
                element_type="button",
                position={"x": int(scene_pos.x()), "y": int(scene_pos.y())},
                size={"width": 100, "height": 40},
                properties={"label": "Button", "background_color": "#5a6270", "text_color": "#ffffff"}
            )
            self.preview_item = ButtonGraphicsItem(default_data)
            self.preview_item.setOpacity(0.5)
            self._scene.addItem(self.preview_item)
        else:
            self.preview_item.setPos(scene_pos.x(), scene_pos.y())

    def _place_button(self, scene_pos) -> None:
        """Place a new button element at the given scene position."""
        if not self.screen_data:
            return
        # Create new button element data
        new_button = {
            "instance_id": f"button_{len(self.screen_data.get('children', [])) + 1}",
            "type": "button",
            "position": {"x": int(scene_pos.x()), "y": int(scene_pos.y())},
            "size": {"width": 100, "height": 40},
            "properties": {"label": "Button", "background_color": "#5a6270", "text_color": "#ffffff"}
        }
        # Add to screen data children
        self.screen_data.setdefault("children", []).append(new_button)
        # Notify screen service of modification
        screen_service.notify_screen_update(self.screen_id)
        # Clear preview
        self._clear_placement_preview()

    def _place_drawing_object(self, scene_pos: QPointF) -> None:
        """Place a new drawing object on the canvas."""
        if not self.screen_data:
            return

        tool_type = self.placement_tool
        if not tool_type:
            return

        x, y = int(scene_pos.x()), int(scene_pos.y())
        num_children = len(self.screen_data.get('children', []))
        
        new_element = {
            "instance_id": f"{tool_type}_{num_children + 1}",
            "type": tool_type,
            "position": {"x": x, "y": y},
            "properties": {}
        }

        if tool_type == constants.TOOL_RECTANGLE:
            width, height = 100, 60
            new_element["size"] = {"width": width, "height": height}
            new_element["properties"] = {"x": x, "y": y, "width": width, "height": height, "color": "#5a6270"}
        elif tool_type == constants.TOOL_CIRCLE:
            diameter = 60
            new_element["size"] = {"width": diameter, "height": diameter}
            new_element["properties"] = {"x": x, "y": y, "diameter": diameter, "color": "#5a6270"}
        elif tool_type == constants.TOOL_POLYGON:
            # Default to a triangle, points are relative to the item's position
            points = [[0, 0], [100, 0], [50, -86]]
            new_element["size"] = {"width": 100, "height": 86}
            new_element["properties"] = {"points": points, "color": "#5a6270"}
        elif tool_type == constants.TOOL_TEXT:
            new_element["size"] = {"width": 100, "height": 20}
            new_element["properties"] = {"x": x, "y": y, "text": "Text", "font_size": 14, "color": "#222222"}
        
        if new_element.get("properties"):
            self.screen_data.setdefault("children", []).append(new_element)
            screen_service.notify_screen_update(self.screen_id)

        self._clear_placement_preview()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:

        """Handle mouse release events."""
        scene_pos = self.mapToScene(event.pos())
        if self.active_tool == constants.TOOL_SELECT:
            if self._marquee_active:
                # Finalize marquee selection
                selection_rect = self._marquee_rect_item.rect().normalized()
                self._scene.removeItem(self._marquee_rect_item)
                self._marquee_rect_item = None
                self._marquee_active = False

                items_to_process = []
                for item in self._scene.items(selection_rect):
                    if item is None:
                        continue
                    if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                        item_rect = item.sceneBoundingRect()
                        if selection_rect.contains(item_rect):
                            items_to_process.append(item)

                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    for it in items_to_process:
                        self.selection_manager.toggle_selection(it)
                else:
                    self.selection_manager.clear_selection()
                    for it in items_to_process:
                        self.selection_manager.select_item(it, True)

                event.accept()
                return

            if self.selection_manager._is_moving:
                self.selection_manager.finish_move(scene_pos)
                event.accept()
        super().mouseReleaseEvent(event)

    
    def _on_zoom_changed(self, scale_factor):
        """Handle zoom changes from zoom manager."""
        self._scale_factor = scale_factor
        self.zoom_changed.emit(f"{int(scale_factor * 100)}%")
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel events for zoom."""
        if self.zoom_manager.handle_wheel_event(event):
            return
        super().wheelEvent(event)
        
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for zoom shortcuts."""
        # Delegate to drawing tool if active

        
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            
            # Handle both Ctrl++ and Ctrl+= (same physical key on US keyboards)
            if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                self.zoom_manager.zoom_in()
                event.accept()
                return
            elif key == Qt.Key.Key_Minus:
                self.zoom_manager.zoom_out()
                event.accept()
                return
            elif key == Qt.Key.Key_0:
                self.zoom_manager.zoom_to_100()
                event.accept()
                return
            elif key == Qt.Key.Key_1:
                self.zoom_manager.zoom_to_fit()
                event.accept()
                return
                
        super().keyPressEvent(event)
