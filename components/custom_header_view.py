# components/custom_header_view.py
# Neutral header view: keep default behavior, no custom painting.

from PyQt6.QtWidgets import QHeaderView

class CustomHeaderView(QHeaderView):
    """
    A no-op subclass of QHeaderView so existing imports keep working.
    This intentionally does not override paintSection; result = native look.
    """
    pass
