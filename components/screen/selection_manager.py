from PyQt6.QtCore import QObject, QPointF, pyqtSignal, Qt
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem


class SelectionManager(QObject):
    """Manages item selection and movement within a QGraphicsScene."""

    selection_changed = pyqtSignal(list)
    item_moved = pyqtSignal(str, QPointF, QPointF)

    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        self.selected_items = set()
        self._is_moving = False
        self._move_start_pos = QPointF()
        self._original_positions = {}

    def select_item(
        self, item: QGraphicsItem, multi_select: bool = False
    ):
        """Select a new item, optionally preserving existing selections."""
        if not multi_select:
            self.clear_selection()
        if item not in self.selected_items:
            self.selected_items.add(item)
            try:
                item.setSelected(True)
            except RuntimeError:
                pass
            self.selection_changed.emit(
                [
                    self._get_item_id(i)
                    for i in self.selected_items
                ]
            )

    def toggle_selection(self, item: QGraphicsItem):
        """Toggle selection state of an item."""
        if item in self.selected_items:
            self.deselect_item(item)
        else:
            self.select_item(item, True)

    def deselect_item(self, item: QGraphicsItem):
        """Deselect a single item."""
        if item in self.selected_items:
            self.selected_items.remove(item)
            try:
                item.setSelected(False)
            except RuntimeError:
                pass
            self.selection_changed.emit(
                [
                    self._get_item_id(i)
                    for i in self.selected_items
                ]
            )

    def clear_selection(self):
        """Deselect all items."""
        for item in list(self.selected_items):
            try:
                item.setSelected(False)
            except RuntimeError:
                pass
        self.selected_items.clear()
        self.selection_changed.emit([])

    def start_move(self, scene_pos: QPointF):
        """Begin moving currently selected items."""
        if not self.selected_items:
            return
        self._is_moving = True
        self._move_start_pos = QPointF(scene_pos)
        self._original_positions = {
            self._get_item_id(item): QPointF(item.pos())
            for item in self.selected_items
        }
        # Mark items as moving so TransformHandler can skip painting
        for item in self.selected_items:
            try:
                item._is_moving = True
            except Exception:
                pass

    def update_move(self, scene_pos: QPointF):
        """Update positions of selected items during a move."""
        if not self._is_moving:
            return
        delta = scene_pos - self._move_start_pos
        for item in self.selected_items:
            item_id = self._get_item_id(item)
            if item_id in self._original_positions:
                original_pos = self._original_positions[item_id]
                new_pos = original_pos + delta
                # setPos triggers itemChange on the item
                item.setPos(new_pos)

    def finish_move(self, scene_pos: QPointF):
        """Finalize positions when moving ends and emit move signal."""
        if not self._is_moving:
            return
        delta = scene_pos - self._move_start_pos
        for item in self.selected_items:
            item_id = self._get_item_id(item)
            original_pos = self._original_positions.get(
                item_id, item.pos()
            )
            new_pos = original_pos + delta
            # Emit move event
            self.item_moved.emit(
                item_id, original_pos, new_pos
            )
            # Clear moving flag and repaint handles
            try:
                item._is_moving = False
                if hasattr(
                    item, "transform_handler"
                ):
                    item.transform_handler.invalidate_cache()
                item.update()
            except Exception:
                pass

        self._is_moving = False
        self._original_positions.clear()

    def cancel_move(self):
        """Cancel an ongoing move and restore original positions."""
        if self._is_moving:
            for item in self.selected_items:
                item_id = self._get_item_id(item)
                if (
                    item_id
                    in self._original_positions
                ):
                    item.setPos(
                        self._original_positions[item_id]
                    )
                    try:
                        item._is_moving = False
                        if hasattr(
                            item, "transform_handler"
                        ):
                            item.transform_handler.invalidate_cache()
                        item.update()
                    except Exception:
                        pass
            self._is_moving = False
            self._original_positions.clear()

    def get_selected_item_ids(self):
        """Return the IDs of all selected items."""
        return [
            self._get_item_id(item)
            for item in self.selected_items
        ]

    def _get_item_id(self, item: QGraphicsItem) -> str:
        """Return a stable identifier for an item."""
        element_data = getattr(item, "element_data", None)
        if (
            element_data is not None
            and hasattr(element_data, "element_id")
        ):
            return getattr(
                element_data, "element_id"
            )
        # Fall back to the instance ID stored in the item's user data
        # (role 0), which is used by generic drawing tools.  If not
        # available, use the Python object id as a last resort.
        item_id = item.data(0)
        if item_id is not None:
            return str(item_id)
        return str(id(item))

    def handle_mouse_press(self, event, item=None):
        """Delegate selection based on modifier keys."""
        if (
            event.modifiers()
            & Qt.KeyboardModifier.ShiftModifier
            or event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):
            if item:
                self.toggle_selection(item)
        else:
            if item:
                self.select_item(item)
            else:
                self.clear_selection()

    def handle_key_press(self, event):
        """Handle keyboard shortcuts for deletion and select-all."""
        key = event.key()
        if key == Qt.Key.Key_Delete:
            for item in list(self.selected_items):
                try:
                    self.scene.removeItem(item)
                except Exception:
                    pass
            self.clear_selection()
        elif (
            key == Qt.Key.Key_A
            and event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):
            # Select all selectable items in the scene
            for item in self.scene.items():
                if (
                    item.flags()
                    & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                ):
                    self.select_item(item, True)
