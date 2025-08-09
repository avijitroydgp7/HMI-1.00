# dialogs/tag_browser_dialog.py
# A reusable dialog for browsing and selecting tags from all databases.

from PyQt6.QtWidgets import (
    QVBoxLayout, QTreeWidget, QTreeWidgetItem, QDialogButtonBox, 
    QHeaderView, QLineEdit, QTreeWidgetItemIterator, QHBoxLayout, QWidget
)
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtCore import Qt, QRect
from typing import List, Optional, Tuple, Any

from services.tag_data_service import tag_data_service
from .base_dialog import CustomDialog
from utils.icon_manager import IconManager

class TagTreeItem(QTreeWidgetItem):
    """
    A custom tree widget item to allow for proper sorting by text in any column.
    """
    def __lt__(self, other: QTreeWidgetItem):
        tree = self.treeWidget()
        if not tree:
            return super().__lt__(other)
        
        column = tree.sortColumn()
        return self.text(column).lower() < other.text(column).lower()

class CustomTagTreeWidget(QTreeWidget):
    """
    A custom tree widget that uses custom (+) / (-) icons for expand/collapse
    similar to the tag table implementation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Disable default double-click expansion
        self.setExpandsOnDoubleClick(False)
        # Standardize indentation
        self.setIndentation(20)
        self.setRootIsDecorated(True)
        
    def mousePressEvent(self, event):
        """Handle mouse clicks for custom expand/collapse icons."""
        index = self.indexAt(event.pos())
        if not index.isValid():
            super().mousePressEvent(event)
            return

        # Get the branch rectangle
        branch_rect = self.visualRect(index)
        
        # Calculate indicator position
        indent = self.indentation()
        icon_size = 16
        
        level = 0
        parent = index.parent()
        while parent.isValid():
            level += 1
            parent = parent.parent()
        
        indicator_x = branch_rect.left() + (level * indent) + (indent - icon_size) // 2
        indicator_y = branch_rect.top() + (branch_rect.height() - icon_size) // 2
        
        indicator_rect = QRect(indicator_x, indicator_y, icon_size, icon_size)
        
        # Check if click is on the branch indicator
        if indicator_rect.contains(event.pos()):
            item = self.itemFromIndex(index)
            if item and item.childCount() > 0:
                is_expanded = self.isExpanded(index)
                self.setExpanded(index, not is_expanded)
                return

        # Default behavior for other clicks
        super().mousePressEvent(event)

    def drawBranches(self, painter: QPainter, rect: QRect, index):
        """Draw custom (+) / (-) icons for expand/collapse."""
        # First draw the base branches
        super().drawBranches(painter, rect, index)
        
        item = self.itemFromIndex(index)
        if not item:
            return
            
        # Only draw custom icons for items with children
        if item.childCount() == 0:
            return
            
        # Determine if expanded
        is_expanded = self.isExpanded(index)
        
        # Use the same icons as tag table
        icon_name = 'fa5s.minus-square' if is_expanded else 'fa5s.plus-square'
        icon = IconManager.create_icon(icon_name)
        icon_size = 16
        
        # Calculate position
        level = 0
        parent = index.parent()
        while parent.isValid():
            level += 1
            parent = parent.parent()
            
        indent = self.indentation()
        icon_x = rect.left() + (level * indent) + (indent - icon_size) // 2
        icon_y = rect.top() + (rect.height() - icon_size) // 2
        
        # Draw the icon
        icon.paint(painter, icon_x, icon_y, icon_size, icon_size)

class TagBrowserDialog(CustomDialog):
    """
    A dialog that allows users to browse all tag databases and select a tag.
    Includes a dynamic search field and per-column filters.
    """
    def __init__(self, parent=None, allowed_types: Optional[List[str]] = None, allow_arrays: bool = True, preselected_tag: Optional[Tuple[str, str, str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Tag Browser")
        self.setMinimumSize(600, 500)
        self.allowed_types = allowed_types
        self.allow_arrays = allow_arrays
        self.selected_tag_info = None
        self.preselected_tag = preselected_tag

        content_layout = self.get_content_layout()

        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 5, 0, 5)
        filter_layout.setSpacing(5)

        self.name_filter_input = QLineEdit(); self.name_filter_input.setPlaceholderText("Filter by Name..."); self.name_filter_input.textChanged.connect(self._filter_tree)
        self.type_filter_input = QLineEdit(); self.type_filter_input.setPlaceholderText("Filter by Type..."); self.type_filter_input.textChanged.connect(self._filter_tree)
        self.comment_filter_input = QLineEdit(); self.comment_filter_input.setPlaceholderText("Filter by Comment..."); self.comment_filter_input.textChanged.connect(self._filter_tree)

        filter_layout.addWidget(self.name_filter_input)
        filter_layout.addWidget(self.type_filter_input)
        filter_layout.addWidget(self.comment_filter_input)
        
        self.tree = CustomTagTreeWidget()
        self.tree.setHeaderLabels(["Name", "Data Type", "Comment"])
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.tree.itemDoubleClicked.connect(self.accept)
        
        content_layout.addWidget(filter_widget)
        content_layout.addWidget(self.tree)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        content_layout.addWidget(self.button_box)

        self._populate_tree()
        self._highlight_preselected_tag()

    def _populate_tree(self):
        """
        Fills the tree with tags, filtering by allowed types and array status.
        Handles synonyms for data types (e.g., INT and INT16).
        """
        self.tree.clear()
        all_dbs = tag_data_service.get_all_tag_databases()

        # Map of UI-facing types to possible data-layer types (case-insensitive)
        type_synonyms = {
            "INT16": ["INT16", "INT"],
            "INT32": ["INT32", "DINT"],
            "REAL": ["REAL"],
            "BOOL": ["BOOL"],
        }

        # Create a flat list of all possible valid data layer types based on self.allowed_types
        valid_data_layer_types = []
        if self.allowed_types:
            for ui_type in self.allowed_types:
                # Add all known synonyms for the allowed UI type
                valid_data_layer_types.extend(type_synonyms.get(ui_type.upper(), [ui_type.upper()]))
        
        # Make the check list case-insensitive for robustness
        valid_data_layer_types = [t.upper() for t in valid_data_layer_types]

        for db_id, db_data in all_dbs.items():
            db_name = db_data.get('name', 'Unnamed DB')
            db_item = TagTreeItem(self.tree, [db_name])
            db_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "db", "id": db_id})

            for tag in db_data.get('tags', []):
                data_type = tag.get('data_type', 'N/A')
                is_array = bool(tag.get('array_dims'))

                # --- Filtering Logic ---
                # 1. Filter by allowed data types, considering synonyms
                if self.allowed_types and data_type.upper() not in valid_data_layer_types:
                    continue
                
                # 2. Filter out arrays if they are not allowed
                if not self.allow_arrays and is_array:
                    continue

                tag_item = TagTreeItem(db_item, [tag.get('name'), data_type, tag.get('comment')])
                tag_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "tag", "db_id": db_id, "db_name": db_name, "tag_name": tag.get('name')})
        
        self.tree.expandAll()

    def _filter_tree(self):
        """Dynamically filters the tree view based on the search text in all filter fields."""
        name_filter = self.name_filter_input.text().lower()
        type_filter = self.type_filter_input.text().lower()
        comment_filter = self.comment_filter_input.text().lower()
        
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            # Only filter tag items (children of database items)
            if item.parent():
                name_match = name_filter in item.text(0).lower()
                type_match = type_filter in item.text(1).lower()
                comment_match = comment_filter in item.text(2).lower()
                item.setHidden(not (name_match and type_match and comment_match))
            iterator += 1
            
        # Hide parent (database) items if all their children are hidden
        for i in range(self.tree.topLevelItemCount()):
            db_item = self.tree.topLevelItem(i)
            has_visible_child = False
            for j in range(db_item.childCount()):
                if not db_item.child(j).isHidden():
                    has_visible_child = True
                    break
            db_item.setHidden(not has_visible_child)

    def accept(self):
        """Overrides accept to store the selected tag before closing."""
        selected_item = self.tree.currentItem()
        if not selected_item or not selected_item.parent():
            return
        
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and item_data.get("type") == "tag":
            self.selected_tag_info = (
                item_data.get("db_id"),
                item_data.get("db_name"),
                item_data.get("tag_name")
            )
            super().accept()

    def _highlight_preselected_tag(self):
        """Highlights the preselected tag in the tree view and makes used tags bold."""
        if not self.preselected_tag:
            return
            
        db_id, db_name, tag_name = self.preselected_tag
        
        # Create bold font for preselected items
        from PyQt6.QtGui import QFont
        bold_font = QFont()
        bold_font.setBold(True)
        
        # Iterate through all items to find and style matching tags
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            
            if item_data and item_data.get("type") == "tag":
                if (item_data.get("db_id") == db_id and 
                    item_data.get("db_name") == db_name and 
                    item_data.get("tag_name") == tag_name):
                    
                    # Apply bold font to the tag item
                    for col in range(item.columnCount()):
                        item.setFont(col, bold_font)
                    
                    # Select and scroll to the item
                    self.tree.setCurrentItem(item)
                    self.tree.scrollToItem(item)
                    
                    # Expand parent if not already expanded
                    parent = item.parent()
                    if parent and not parent.isExpanded():
                        parent.setExpanded(True)
                    
                    break
            iterator += 1

    def get_selected_tag_info(self) -> Optional[Tuple[str, str, str]]:
        """Returns the selected tag's database ID, database name, and tag name."""
        return self.selected_tag_info
