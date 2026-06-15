from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QSpinBox, QDoubleSpinBox

from .base_editor import BaseValueEditor


class NumericValueEditor(BaseValueEditor):
    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
        self._editor = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        if self._field == "publish_year":
            self._editor = QSpinBox()
            self._editor.setRange(1900, 2100)
        else:
            self._editor = QDoubleSpinBox()
            self._editor.setRange(0, 10000)
            self._editor.setDecimals(2)
            self._editor.setSuffix(" MB")

        self._editor.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self._editor)

    def _update_ui(self):
        if self._values:
            try:
                self._editor.setValue(float(self._values[0]))
            except (ValueError, TypeError):
                pass

    def _on_value_changed(self, value):
        self._values = [str(value)]
        self._notify_changed()

    def get_value(self) -> float:
        return self._editor.value()
