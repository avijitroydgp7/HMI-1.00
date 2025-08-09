# components/screen/screen_manager_widget.py
"""
ScreenManagerWidget - A widget for managing screens in the HMI Designer.
This widget provides functionality for creating, editing, and organizing screens.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, Qt, QRect
from PyQt6.QtGui import QAction, QPainter, QMouseEvent

from services.screen_data_service import screen_service
from services.command_history_service import command_history_service
from services.commands import AddScreenCommand, RemoveScreenCommand
from dialogs.screen_properties_dialog import ScreenPropertiesDialog
from utils.icon_manager import IconManager


class ScreenType(Enum):
    """Enumeration of screen types for better type safety."""
    BASE = "base"
    WINDOW = "window"
    REPORT = "report"


@dataclass
class ScreenItemData:
    """Data structure for screen items to improve type safety."""
    screen_id: str
    screen_type: ScreenType
    number: int
    name: str
    description: str = ""


class ScreenTreeWidget(QTreeWidget):
    """Custom tree widget with expand/collapse icons for screen management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Disable the default double-click expand/collapse behavior
        self.setExpandsOnDoubleClick(False)
        # Use a fixed indentation for consistent alignment
        self.setIndentation(20)
        self.setRootIsDecorated(True)

    def mousePressEvent(self, event: QMouseEvent):
        """Override mouse press to toggle branch expansion on single click."""
        from PyQt6.QtCore import QModelIndex

        index = self.indexAt(event.pos())
        if not index.isValid():
            super().mousePressEvent(event)
            return

        # Determine if the click is on the branch indicator
        branch_rect = self.visualRect(index)
        indent = self.indentation()
        icon_size = 16

        # Compute the level depth to align the indicator correctly
        level = 0
        parent_index = index.parent()
        while parent_index.isValid():
            level += 1
            parent_index = parent_index.parent()

        indicator_x = (
            branch_rect.left()
            + (level * indent)
            + (indent - icon_size) // 2
        )
        indicator_y = branch_rect.top() + (
            branch_rect.height() - icon_size
        ) // 2
        indicator_rect = QRect(
            indicator_x,
            indicator_y,
            icon_size,
            icon_size,
        )

        # Toggle expand/collapse if the click falls within the indicator
        if indicator_rect.contains(event.pos()):
            item = self.itemFromIndex(index)
            if item:
                has_children = item.childCount() > 0
                show_indicator_policy = (
                    item.childIndicatorPolicy()
                    == QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )
                if has_children or show_indicator_policy:
                    self.setExpanded(index, not self.isExpanded(index))
                    return

        # Otherwise, use default behavior
        super().mousePressEvent(event)

    def drawBranches(self, painter: QPainter, rect: QRect, index):
        """Draw custom expand/collapse icons over default branch indicators."""
        # Draw default branch lines and indicator first
        super().drawBranches(painter, rect, index)

        # Only draw icons if item has children
        item = self.itemFromIndex(index)
        if not item or item.childCount() == 0:
            return

        # Choose plus or minus icon based on expansion state
        is_expanded = self.isExpanded(index)
        icon_name = (
            "fa5s.minus-square" if is_expanded else "fa5s.plus-square"
        )
        icon = IconManager.create_icon(icon_name)
        icon_size = 16

        # Compute icon position relative to tree level
        level = 0
        parent_index = index.parent()
        while parent_index.isValid():
            level += 1
            parent_index = parent_index.parent()

        indent = self.indentation()
        icon_x = rect.left() + (level * indent) + (
            indent - icon_size
        ) // 2
        icon_y = rect.top() + (
            rect.height() - icon_size
        ) // 2

        # Paint the icon
        icon.paint(painter, icon_x, icon_y, icon_size, icon_size)


class ScreenManagerWidget(QWidget):
    """
    Widget for managing screens in the HMI Designer with improved architecture.
    """

    screen_open_requested = pyqtSignal(str)  # emitted with screen_id
    selection_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the ScreenManagerWidget."""
        super().__init__(parent)
        self._screen_items: Dict[str, QTreeWidgetItem] = {}
        self._category_items: Dict[ScreenType, QTreeWidgetItem] = {}

        self._setup_ui()
        self._connect_signals()
        self._populate_screen_list()

        # Backward compatibility: provide `tree` alias
        self.tree = self.screen_tree

    def _handle_general_design_save(self, design_data: dict) -> None:
        """Handle saving generic design data from the screen-design dialog."""
        print("General Screen Design saved:", design_data)

    def update_active_screen_highlight(
        self, screen_id: Optional[str]
    ) -> None:
        """Highlight the active screen in the tree view."""
        # Clear all highlights
        for item in self._screen_items.values():
            for col in range(item.columnCount()):
                item.setBackground(
                    col, Qt.GlobalColor.transparent
                )

        # Highlight the selected item
        if screen_id and screen_id in self._screen_items:
            item = self._screen_items[screen_id]
            for col in range(item.columnCount()):
                item.setBackground(
                    col, Qt.GlobalColor.darkGray
                )

    def _setup_ui(self) -> None:
        """Build the tree widget layout and configure signals."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.screen_tree = ScreenTreeWidget()
        self.screen_tree.setHeaderLabels(["Screens"])
        self.screen_tree.setHeaderHidden(True)
        self.screen_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.screen_tree.customContextMenuRequested.connect(
            self._show_context_menu
        )
        self.screen_tree.itemDoubleClicked.connect(
            self._on_item_double_clicked
        )
        self.screen_tree.itemSelectionChanged.connect(
            self._on_selection_changed
        )

        # Ensure consistent indentation and decoration
        self.screen_tree.setIndentation(20)
        self.screen_tree.setRootIsDecorated(True)
        self.screen_tree.setExpandsOnDoubleClick(False)

        layout.addWidget(self.screen_tree)

    def _connect_signals(self) -> None:
        """Connect to screen-service signals."""
        screen_service.screen_list_changed.connect(
            self._populate_screen_list
        )

    def _populate_screen_list(self) -> None:
        """Populate the tree with category nodes and screen nodes."""
        self.screen_tree.clear()
        self._screen_items.clear()
        self._category_items.clear()

        # Top-level design node
        design_item = QTreeWidgetItem(self.screen_tree)
        design_item.setText(0, "Screen Design")
        design_item.setIcon(
            0,
            IconManager.create_icon(
                "fa5s.palette",
                color="#ff9800",
                size=16,
            ),
        )
        design_item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            "screen_design_property",
        )

        # Create category nodes
        for screen_type in ScreenType:
            category_item = self._create_category_item(screen_type)
            self._category_items[screen_type] = category_item

        # Add screens to categories
        screens = screen_service.get_all_screens()
        for screen_id, screen_data in screens.items():
            screen_type = ScreenType(
                screen_data.get("type", "base")
            )
            screen_item = self._create_screen_item(
                screen_id, screen_data
            )
            if screen_type in self._category_items:
                self._category_items[screen_type].addChild(
                    screen_item
                )
                self._screen_items[screen_id] = screen_item

        # Expand categories by default
        for category_item in self._category_items.values():
            category_item.setExpanded(True)

        self.screen_tree.resizeColumnToContents(0)

    def _create_category_item(
        self, screen_type: ScreenType
    ) -> QTreeWidgetItem:
        """Create and return a category node for a given screen type."""
        category_names = {
            ScreenType.BASE: "Base Screens",
            ScreenType.WINDOW: "Window Screens",
            ScreenType.REPORT: "Report Screens",
        }
        icons = {
            ScreenType.BASE: "fa5s.window-maximize",
            ScreenType.WINDOW: "fa5s.window-restore",
            ScreenType.REPORT: "fa5s.file-alt",
        }

        item = QTreeWidgetItem(self.screen_tree)
        item.setText(0, category_names[screen_type])
        item.setIcon(
            0,
            IconManager.create_icon(
                icons[screen_type], color="#5dadec"
            ),
        )
        item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            f"category_{screen_type.value}",
        )
        return item

    def _create_screen_item(
        self, screen_id: str, screen_data: Dict[str, Any]
    ) -> QTreeWidgetItem:
        """Create a screen leaf node with an appropriate icon and label."""
        screen_item = QTreeWidgetItem()

        number = str(screen_data.get("number", screen_id))
        name = screen_data.get(
            "name", f"Screen {screen_id}"
        )
        screen_type = ScreenType(
            screen_data.get("type", "base")
        )

        # Map screen type to icon
        screen_type_icons = {
            ScreenType.BASE: "fa5s.window-maximize",
            ScreenType.WINDOW: "fa5s.window-restore",
            ScreenType.REPORT: "fa5s.file-alt",
        }

        icon_name = screen_type_icons.get(
            screen_type, "fa5s.window-maximize"
        )
        screen_icon = IconManager.create_icon(
            icon_name, color="#c8cdd4", size=16
        )

        screen_item.setIcon(0, screen_icon)
        screen_item.setText(0, f"[{number}] - {name}")
        screen_item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            screen_id,
        )
        screen_item.setData(
            0,
            Qt.ItemDataRole.UserRole + 1,
            screen_data.get("number"),
        )

        return screen_item

    def _on_item_double_clicked(
        self, item: QTreeWidgetItem, column: int
    ) -> None:
        """Handle double clicks to open design or screen properties."""
        item_data = item.data(
            0, Qt.ItemDataRole.UserRole
        )

        if item_data == "screen_design_property":
            # Launch the generic screen-design dialog
            from dialogs.screen_design_dialog import ScreenDesignDialog

            dialog = ScreenDesignDialog(
                parent=self,
                screen_id=None,
                current_design={},
            )
            dialog.design_saved.connect(
                lambda design_data: self._handle_general_design_save(
                    design_data
                )
            )
            dialog.exec()
        elif (
            item_data
            and item_data.startswith("design_")
        ):
            # Launch the screen-specific design dialog
            screen_id = item_data.replace("design_", "")
            self._open_screen_design_dialog(screen_id)
        elif (
            item_data
            and not item_data.startswith("category_")
        ):
            # Emit to open the selected screen
            self.screen_open_requested.emit(
                item_data
            )

    def _on_selection_changed(self) -> None:
        """Forward selection changes."""
        self.selection_changed.emit()

    def _show_context_menu(self, position) -> None:
        """Display a context menu based on the clicked item type."""
        item = self.screen_tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        item_type = item.data(
            0, Qt.ItemDataRole.UserRole
        )

        if isinstance(item_type, str) and item_type.startswith(
            "category_"
        ):
            # Category context menu
            screen_type = ScreenType(
                item_type.split("_")[1]
            )
            self._add_category_menu_actions(menu, screen_type)
        else:
            # Screen context menu
            self._add_screen_menu_actions(menu, item)

        viewport = self.screen_tree.viewport()
        if viewport:
            menu.exec(
                viewport.mapToGlobal(position)
            )

    def _add_category_menu_actions(
        self, menu: QMenu, screen_type: ScreenType
    ) -> None:
        """Populate the context menu for a category item."""
        add_action = QAction("Add New Screen", self)
        add_action.triggered.connect(
            lambda: self._create_new_screen(screen_type)
        )
        menu.addAction(add_action)

    def _add_screen_menu_actions(
        self, menu: QMenu, item: QTreeWidgetItem
    ) -> None:
        """Populate the context menu for a screen item."""
        open_action = QAction("Open", self)
        open_action.triggered.connect(
            lambda: self._open_screen(item)
        )
        menu.addAction(open_action)

        menu.addSeparator()

        edit_action = QAction(
            "Edit Properties...", self
        )
        edit_action.triggered.connect(
            lambda: self._edit_screen(item)
        )
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            lambda: self._delete_screen(item)
        )
        menu.addAction(delete_action)

    def _open_screen(self, item: QTreeWidgetItem) -> None:
        """Emit a request to open the screen represented by the tree item."""
        screen_id = item.data(
            0, Qt.ItemDataRole.UserRole
        )
        self.screen_open_requested.emit(screen_id)

    def _create_new_screen(
        self, screen_type: ScreenType
    ) -> None:
        """Create a new screen and push it onto the command history."""
        dialog = ScreenPropertiesDialog(
            screen_type.value, self
        )
        if dialog.exec():
            screen_data = dialog.get_data()
            screen_data["type"] = screen_type.value
            command = AddScreenCommand(screen_data)
            command_history_service.add_command(
                command
            )

    def _edit_screen(
        self, item: QTreeWidgetItem
    ) -> None:
        """Open the properties dialog for editing the selected screen."""
        screen_id = item.data(
            0, Qt.ItemDataRole.UserRole
        )
        screen_data = screen_service.get_screen(screen_id)
        if not screen_data:
            return

        dialog = ScreenPropertiesDialog(
            ScreenType(
                screen_data.get("type", "base")
            ).value,
            self,
            screen_data,
        )
        if dialog.exec():
            new_data = dialog.get_data()
            new_data["type"] = screen_data.get(
                "type", "base"
            )
            from services.commands import (
                UpdateScreenPropertiesCommand,
            )

            command = UpdateScreenPropertiesCommand(
                screen_id,
                new_data,
                screen_data,
            )
            command_history_service.add_command(command)

    def _delete_screen(
        self, item: QTreeWidgetItem
    ) -> None:
        """Prompt for confirmation and then delete the screen."""
        screen_id = item.data(
            0, Qt.ItemDataRole.UserRole
        )
        screen_name = item.text(0)

        reply = QMessageBox.question(
            self,
            "Delete Screen",
            f"Are you sure you want to delete '{screen_name}'?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            reply
            == QMessageBox.StandardButton.Yes
        ):
            command = RemoveScreenCommand(screen_id)
            command_history_service.add_command(
                command
            )

    def _open_screen_design_dialog(
        self, screen_id: str
    ) -> None:
        """Open the screen-design dialog for a specific screen."""
        from dialogs.screen_design_dialog import (
            ScreenDesignDialog,
        )

        screen_data = screen_service.get_screen(
            screen_id
        )
        if not screen_data:
            return

        current_design = screen_data.get(
            "design", {}
        )
        dialog = ScreenDesignDialog(
            parent=self,
            screen_id=screen_id,
            current_design=current_design,
        )
        dialog.design_saved.connect(
            lambda design_data: self._save_screen_design(
                screen_id, design_data
            )
        )
        dialog.exec()

    def _save_screen_design(
        self, screen_id: str, design_data: dict
    ) -> None:
        """Save the updated screen design via command history."""
        screen_data = screen_service.get_screen(
            screen_id
        )
        if not screen_data:
            return
        screen_data["design"] = design_data
        from services.commands import (
            UpdateScreenPropertiesCommand,
        )

        command = UpdateScreenPropertiesCommand(
            screen_id,
            screen_data,
            screen_service.get_screen(screen_id),
        )
        command_history_service.add_command(
            command
        )
