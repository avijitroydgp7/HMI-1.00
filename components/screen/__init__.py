"""Screen components package for the HMI Designer.

This package provides the core screen management and editing functionality:
- ScreenManagerWidget: Tree-based screen management
- ScreenWidget: Individual screen display and editing
- ScreenCanvas: Graphics canvas for screen content
- TransformHandler: Handles transformation of drawing objects
- BaseDrawingItem: Base class for all drawing items with transform capabilities
"""

from .screen_manager_widget import ScreenManagerWidget, ScreenType
from .screen_widget import ScreenWidget, ScreenCanvas, ScreenElement, ElementData
from .transform_handler import TransformHandler
from .base_drawing_item import BaseDrawingItem

__all__ = [
    'ScreenManagerWidget',
    'ScreenWidget', 
    'ScreenCanvas',
    'ScreenElement',
    'ElementData',
    'ScreenType',
    'TransformHandler',
    'BaseDrawingItem'
]
