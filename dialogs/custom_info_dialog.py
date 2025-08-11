# dialogs/custom_info_dialog.py
# A custom, stylable dialog for showing simple informational messages.

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from .base_dialog import CustomDialog

class CustomInfoDialog(CustomDialog):
    """A dialog for showing information, warnings, or errors with a single "OK" button."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(400)

        content_layout = self.get_content_layout()
        
        # Main content layout
        main_content_layout = QVBoxLayout()
        main_content_layout.setSpacing(15)
        
        self.info_label = QLabel("Information text goes here.")
        self.info_label.setWordWrap(True)
        main_content_layout.addWidget(self.info_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("OK")
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        main_content_layout.addLayout(button_layout)
        content_layout.addLayout(main_content_layout)
