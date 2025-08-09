# services/screen_data_service.py
"""
Service for managing screen data in the HMI Designer application.
This service handles screen creation, modification, deletion, and serialization.
"""

from PyQt6.QtCore import pyqtSignal, QObject
import copy
from typing import Dict, Any, Optional, List, Tuple

class ScreenService(QObject):
    """
    Service class for managing screen data.
    Inherits from QObject to support Qt signals.
    """
    
    # Signals for notifying UI components of changes
    screen_list_changed = pyqtSignal()
    screen_modified = pyqtSignal(str)  # Signal with screen ID
    
    def __init__(self):
        super().__init__()
        self._screens: Dict[str, Dict[str, Any]] = {}
        self._next_id = 1
    
    def load_from_project(self, project_data: Dict[str, Any]) -> None:
        """Load screen data from project data."""
        self._screens = project_data.get("screens", {})
        # Update next_id to avoid conflicts
        if self._screens:
            max_id = max(int(screen_id) for screen_id in self._screens.keys() if screen_id.isdigit())
            self._next_id = max_id + 1
    
    def serialize_for_project(self) -> Dict[str, Any]:
        """Serialize screen data for saving to project file."""
        return {"screens": copy.deepcopy(self._screens)}
    
    def clear_all(self) -> None:
        """Clear all screen data."""
        self._screens.clear()
        self._next_id = 1
        self.screen_list_changed.emit()
    
    def get_screen(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Get screen data by ID."""
        return self._screens.get(screen_id)
    
    def get_all_screens(self) -> Dict[str, Dict[str, Any]]:
        """Get all screens."""
        return copy.deepcopy(self._screens)
    
    def is_screen_number_unique(self, screen_type: str, screen_number: int, exclude_id: Optional[str] = None) -> bool:
        """Check if a screen number is unique for a given screen type."""
        for screen_id, screen_data in self._screens.items():
            if screen_id == exclude_id:
                continue
            if screen_data.get('type') == screen_type and screen_data.get('number') == screen_number:
                return False
        return True
    
    def _get_new_screen_id(self) -> str:
        """Generate a new unique screen ID."""
        new_id = str(self._next_id)
        self._next_id += 1
        return new_id
    
    def _perform_add_screen(self, screen_data: Dict[str, Any], screen_id: Optional[str] = None) -> str:
        """Internal method to add a screen."""
        if screen_id is None:
            screen_id = self._get_new_screen_id()
        
        screen_data_with_id = copy.deepcopy(screen_data)
        screen_data_with_id['id'] = screen_id
        screen_data_with_id.setdefault('children', [])
        
        self._screens[screen_id] = screen_data_with_id
        return screen_id
    
    def _perform_remove_screen(self, screen_id: str) -> None:
        """Internal method to remove a screen."""
        if screen_id in self._screens:
            del self._screens[screen_id]
    
    def _perform_update_screen(self, screen_id: str, new_data: Dict[str, Any]) -> None:
        """Internal method to update screen data."""
        if screen_id in self._screens:
            # Preserve children data
            children = self._screens[screen_id].get('children', [])
            self._screens[screen_id].update(new_data)
            self._screens[screen_id]['children'] = children
    
    def _find_child_references(self, screen_id: str) -> List[Tuple[str, Dict]]:
        """Find all references to a screen as a child in other screens."""
        references = []
        for parent_id, parent_data in self._screens.items():
            children = parent_data.get('children', [])
            for child in children[:]:  # Use slice copy to avoid modification during iteration
                if child.get('screen_id') == screen_id:
                    references.append((parent_id, copy.deepcopy(child)))
        return references
    
    def _perform_add_child(self, parent_id: str, child_data: Dict[str, Any]) -> None:
        """Internal method to add a child to a screen."""
        if parent_id in self._screens:
            self._screens[parent_id].setdefault('children', []).append(child_data)
    
    def _perform_remove_child(self, parent_id: str, instance_id: str) -> None:
        """Internal method to remove a child from a screen."""
        if parent_id in self._screens:
            children = self._screens[parent_id].get('children', [])
            self._screens[parent_id]['children'] = [
                child for child in children if child.get('instance_id') != instance_id
            ]
    
    def _perform_update_child_position(self, parent_id: str, instance_id: str, new_pos: Dict[str, int]) -> None:
        """Internal method to update a child's position."""
        if parent_id in self._screens:
            children = self._screens[parent_id].get('children', [])
            for child in children:
                if child.get('instance_id') == instance_id:
                    child['position'] = new_pos
                    break
    
    def _perform_update_child_properties(self, parent_id: str, instance_id: str, new_props: Dict[str, Any]) -> None:
        """Internal method to update a child's properties."""
        if parent_id in self._screens:
            children = self._screens[parent_id].get('children', [])
            for child in children:
                if child.get('instance_id') == instance_id:
                    child.update(new_props)
                    break
    
    def notify_screen_update(self, screen_id: str) -> None:
        """Notify that a screen has been updated."""
        self.screen_modified.emit(screen_id)

# Create a singleton instance for the application to use
screen_service = ScreenService()
