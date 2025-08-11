# dialogs/base_dialog.py
# Simplified base dialog using the system title bar.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget


class CustomDialog(QDialog):
    """Base class for application dialogs using the system title bar."""

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Subclasses add their widgets to this content widget
        self.content_widget = QWidget()
        main_layout.addWidget(self.content_widget)

    def get_content_layout(self):
        """Return or create the layout for the dialog's content area."""
        if not self.content_widget.layout():
            content_layout = QVBoxLayout(self.content_widget)
            content_layout.setContentsMargins(15, 15, 15, 15)
            content_layout.setSpacing(10)
        return self.content_widget.layout()
