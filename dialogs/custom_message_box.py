# dialogs/custom_message_box.py
from __future__ import annotations
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import Qt

class CustomMessageBox(QMessageBox):
    """
    Constructible, native-framed message box.
    - If caller didn't set buttons, we choose smart defaults:
        * Title contains "Unsaved" (case-insensitive) OR text contains "save":
              -> Save / Discard / Cancel
        * otherwise:
              -> OK
    - Callers can still setStandardButtons(...) to override explicitly.
    """
    # Expose button enums so existing code can compare results like CustomMessageBox.Save
    Save = QMessageBox.StandardButton.Save
    Discard = QMessageBox.StandardButton.Discard
    Cancel = QMessageBox.StandardButton.Cancel
    Ok = QMessageBox.StandardButton.Ok

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setIcon(QMessageBox.Icon.Question)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        # Track whether caller explicitly set buttons
        self._buttons_explicit = False

    def setStandardButtons(self, buttons):  # type: ignore[override]
        self._buttons_explicit = True
        return super().setStandardButtons(buttons)

    def exec(self) -> QMessageBox.StandardButton:  # type: ignore[override]
        # If caller didn't specify, choose smart defaults
        if not self._buttons_explicit:
            title = (self.windowTitle() or "").lower()
            text = (self.text() or "").lower()
            if ("unsaved" in title) or ("save" in text):
                super().setStandardButtons(
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel
                )
            else:
                super().setStandardButtons(QMessageBox.StandardButton.Ok)
        return super().exec()
