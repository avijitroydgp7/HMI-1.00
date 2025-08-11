# dialogs/base_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

class CustomDialog(QDialog):
    """
    Native (framed) dialog base preserving original API:
    - get_content_layout()
    - Accepts parent, optional title, modal flag
    """
    def __init__(self, parent=None, title: str | None = None, modal: bool = True):
        super().__init__(parent)
        if title:
            self.setWindowTitle(title)
        self.setModal(modal)

        # Native title bar + working close button; DO NOT auto-delete on close
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        # Important: Do NOT set WA_DeleteOnClose here, so callers can safely read widgets after exec()

        # Content area
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._main_layout.setSpacing(8)

        self.content_widget = QWidget(self)
        self._main_layout.addWidget(self.content_widget)

        self._content_layout = None

    def get_content_layout(self):
        if self._content_layout is None:
            self._content_layout = QVBoxLayout(self.content_widget)
            self._content_layout.setContentsMargins(0, 0, 0, 0)
            self._content_layout.setSpacing(8)
        return self._content_layout
