from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QHBoxLayout, QSpinBox, QDoubleSpinBox, QCheckBox
)

from .base_editor import BaseValueEditor


class RangeValueEditor(BaseValueEditor):
    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
        self._min_enabled = False
        self._max_enabled = False
        self._min_editor = None
        self._max_editor = None
        self._min_checkbox = None
        self._max_checkbox = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        if self._field == "publish_year":
            self._min_editor = QSpinBox()
            self._max_editor = QSpinBox()
            for e in (self._min_editor, self._max_editor):
                e.setRange(1900, 2100)
                e.setSpecialValueText(" ")
        else:
            self._min_editor = QDoubleSpinBox()
            self._max_editor = QDoubleSpinBox()
            for e in (self._min_editor, self._max_editor):
                e.setRange(0, 10000)
                e.setDecimals(2)
                e.setSuffix(" MB")
                e.setSpecialValueText(" ")

        self._min_checkbox = QCheckBox("最小")
        self._max_checkbox = QCheckBox("最大")

        self._min_checkbox.toggled.connect(self._on_min_toggled)
        self._max_checkbox.toggled.connect(self._on_max_toggled)
        self._min_editor.valueChanged.connect(self._on_range_changed)
        self._max_editor.valueChanged.connect(self._on_range_changed)

        self._min_editor.setEnabled(False)
        self._max_editor.setEnabled(False)

        self._min_editor.setValue(0)
        self._max_editor.setValue(0)

        min_layout = QHBoxLayout()
        min_layout.setSpacing(4)
        min_layout.addWidget(self._min_checkbox)
        min_layout.addWidget(self._min_editor, 1)

        max_layout = QHBoxLayout()
        max_layout.setSpacing(4)
        max_layout.addWidget(self._max_checkbox)
        max_layout.addWidget(self._max_editor, 1)

        layout.addLayout(min_layout, 1)
        layout.addLayout(max_layout, 1)

    def _on_min_toggled(self, checked):
        self._min_enabled = checked
        self._min_editor.setEnabled(checked)
        self._on_range_changed()

    def _on_max_toggled(self, checked):
        self._max_enabled = checked
        self._max_editor.setEnabled(checked)
        self._on_range_changed()

    def _update_ui(self):
        min_val = None
        max_val = None

        if len(self._values) >= 1:
            v = self._values[0]
            if v is not None and str(v).strip() != "":
                min_val = v

        if len(self._values) >= 2:
            v = self._values[1]
            if v is not None and str(v).strip() != "":
                max_val = v

        if min_val is not None:
            self._min_checkbox.setChecked(True)
            self._min_editor.setEnabled(True)
            try:
                self._min_editor.setValue(float(min_val))
            except (ValueError, TypeError):
                pass
        else:
            self._min_checkbox.setChecked(False)
            self._min_editor.setEnabled(False)

        if max_val is not None:
            self._max_checkbox.setChecked(True)
            self._max_editor.setEnabled(True)
            try:
                self._max_editor.setValue(float(max_val))
            except (ValueError, TypeError):
                pass
        else:
            self._max_checkbox.setChecked(False)
            self._max_editor.setEnabled(False)

    def _on_range_changed(self):
        min_val = None
        max_val = None

        if self._min_enabled:
            min_val = str(self._min_editor.value())
        if self._max_enabled:
            max_val = str(self._max_editor.value())

        self._values = [min_val, max_val]
        self._notify_changed()

    def is_min_enabled(self) -> bool:
        return self._min_enabled

    def is_max_enabled(self) -> bool:
        return self._max_enabled

    def get_min_value(self) -> Optional[float]:
        return self._min_editor.value() if self._min_enabled else None

    def get_max_value(self) -> Optional[float]:
        return self._max_editor.value() if self._max_enabled else None
