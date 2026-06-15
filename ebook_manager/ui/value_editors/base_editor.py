from __future__ import annotations

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal


class BaseValueEditor(QWidget):
    value_changed = pyqtSignal(list)

    def __init__(self, field: str, parent=None):
        super().__init__(parent)
        self._field = field
        self._values: list = []

    def get_values(self) -> list:
        return self._values

    def set_values(self, values: list):
        self._values = values
        self._update_ui()

    def _update_ui(self):
        pass

    def _notify_changed(self):
        self.value_changed.emit(self._values)
