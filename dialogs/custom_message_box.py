# dialogs/custom_message_box.py
# Message box using the system title bar.

from PyQt6.QtWidgets import QMessageBox


class CustomMessageBox(QMessageBox):
    """Styled message box that relies on the system title bar."""

    Save = QMessageBox.StandardButton.Save
    Discard = QMessageBox.StandardButton.Discard
    Cancel = QMessageBox.StandardButton.Cancel

    def __init__(self, parent=None):
        super().__init__(QMessageBox.Icon.Question, "", "", QMessageBox.StandardButton.NoButton, parent)
        self.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        self.setModal(True)
