# components/toolbar.py
from PyQt6.QtWidgets import QToolBar, QComboBox, QWidget, QSizePolicy

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from utils.icon_manager import IconManager
from utils import constants

class QuickAccessToolBar(QToolBar):
    """
    A customizable toolbar for frequently used actions, typically at the top
    of the window.
    """
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None):

        super().__init__("Quick Access", parent)
        self.setObjectName("QuickAccessToolBar")
        self.setMovable(True)
        self.setIconSize(QSize(16, 16))

        self.new_action = QAction(IconManager.create_icon('fa5s.file'), "New", self)
        self.open_action = QAction(IconManager.create_icon('fa5s.folder-open'), "Open", self)
        self.save_action = QAction(IconManager.create_icon('fa5s.save'), "Save", self)
        
        self.addAction(self.new_action)
        self.addAction(self.open_action)
        self.addAction(self.save_action)
        self.addSeparator()

    def populate_themes(self, themes, current_theme):
        """Legacy method - themes are now handled elsewhere."""
        pass

    def add_clipboard_actions(self, cut_action, copy_action, paste_action):
        """Adds shared clipboard actions to the toolbar."""
        self.addAction(cut_action)
        self.addAction(copy_action)
        self.addAction(paste_action)
        self.addSeparator()

    def add_undo_redo_actions(self, undo_action, redo_action):
        """Adds shared undo/redo actions to the toolbar."""
        self.addAction(undo_action)
        self.addAction(redo_action)
        self.addSeparator()

    def add_view_action(self, action):
        """Adds a shared view toggle action to the toolbar."""
        self.addAction(action)

class ToolsToolbar(QToolBar):
    """
    A toolbar that provides a selection of design tools.
    """

    def __init__(self, action_group: QActionGroup, parent=None):
        super().__init__("Tools", parent)
        self.setObjectName("ToolsToolbar")
        self.setMovable(True)
        self.setFloatable(True)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setIconSize(QSize(20, 20))
        self._action_group = action_group
        self._create_actions()

    def _create_actions(self):
        """Creates the tool actions and adds them to the toolbar."""
        tools = [
            {"id": constants.TOOL_SELECT, "name": "Select Tool", "icon": "fa5s.mouse-pointer", "shortcut": "V", "checked": True},
            {"id": constants.TOOL_BUTTON, "name": "Button Tool", "icon": "fa5s.hand-pointer", "shortcut": "B", "checked": False},
        ]

        for tool in tools:
            action = QAction(IconManager.create_icon(tool["icon"]), tool["name"], self)
            action.setToolTip(f"{tool['name']} ({tool['shortcut']})")
            action.setShortcut(tool["shortcut"])
            action.setCheckable(True)
            action.setChecked(tool["checked"])
            action.setData(tool["id"])
            self._action_group.addAction(action)
            self.addAction(action)

    def set_active_tool(self, tool_id: str):
        """Programmatically sets the active tool in the toolbar."""
        for action in self._action_group.actions():
            if action.data() == tool_id:
                action.setChecked(True)
                break

class DrawingToolbar(QToolBar):
    """A toolbar for drawing various shapes and objects."""

    def __init__(self, action_group: QActionGroup, parent=None):
        super().__init__("Drawing", parent)
        self.setObjectName("DrawingToolbar")
        self.setMovable(True)
        self.setFloatable(True)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setIconSize(QSize(20, 20))
        self._action_group = action_group
        self._create_actions()

    def _create_actions(self):
        """Creates the drawing tool actions and adds them to the toolbar."""
        tools = [
            {"id": constants.TOOL_TEXT, "name": "Text", "icon": "fa5s.font", "shortcut": "T"},
            {"id": constants.TOOL_LINE, "name": "Line", "icon": "fa5s.slash", "shortcut": "L"},
            {"id": constants.TOOL_POLYLINE, "name": "Polyline", "icon": "fa5s.draw-polygon", "shortcut": "P"},
            {"id": constants.TOOL_RECTANGLE, "name": "Rectangle", "icon": "fa5s.square-full", "shortcut": "R"},
            {"id": constants.TOOL_POLYGON, "name": "Polygon", "icon": "fa5s.shapes", "shortcut": ""},
            {"id": constants.TOOL_CIRCLE, "name": "Circle", "icon": "fa5s.circle", "shortcut": "C"},
            {"id": constants.TOOL_ARC, "name": "Arc", "icon": "fa5s.drafting-compass", "shortcut": "A"},
            {"id": constants.TOOL_SECTOR, "name": "Sector", "icon": "fa5s.chart-pie", "shortcut": ""},
            {"id": constants.TOOL_TABLE, "name": "Table", "icon": "fa5s.table", "shortcut": ""},
            {"id": constants.TOOL_SCALE, "name": "Scale", "icon": "fa5s.ruler-combined", "shortcut": ""},
            {"id": constants.TOOL_IMPORT_IMAGE, "name": "Import Image", "icon": "fa5s.image", "shortcut": ""},
            {"id": constants.TOOL_FREEHAND, "name": "Freehand", "icon": "fa5s.pencil-alt", "shortcut": "F"},
            {"id": constants.TOOL_SHAPE_LIBRARY, "name": "Shape Library", "icon": "fa5s.th-large", "shortcut": "S"}
        ]

        for tool in tools:
            action = QAction(IconManager.create_icon(tool["icon"]), tool["name"], self)
            tooltip = f"{tool['name']}"
            if tool.get("shortcut"):
                tooltip += f" ({tool['shortcut']})"
                action.setShortcut(tool["shortcut"])
            action.setToolTip(tooltip)
            action.setCheckable(True)
            action.setChecked(False)
            action.setData(tool["id"])
            self._action_group.addAction(action)
            self.addAction(action)

    def set_active_tool(self, tool_id: str):
        """Programmatically sets the active tool in the toolbar."""
        for action in self._action_group.actions():
            if action.data() == tool_id:
                action.setChecked(True)
                break
