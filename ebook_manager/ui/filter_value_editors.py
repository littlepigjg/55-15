from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QListWidget, QListWidgetItem
)
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


class TextValueEditor(BaseValueEditor):
    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._editor = QLineEdit()
        self._editor.setPlaceholderText("输入关键词，多个用逗号分隔")
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

    def _update_ui(self):
        if self._values:
            self._editor.setText(", ".join(str(v) for v in self._values))

    def _on_text_changed(self, text):
        self._values = [v.strip() for v in text.split(",") if v.strip()]
        self._notify_changed()


class NumericValueEditor(BaseValueEditor):
    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
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


class RangeValueEditor(BaseValueEditor):
    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
        self._min_editor = None
        self._max_editor = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        if self._field == "publish_year":
            self._min_editor = QSpinBox()
            self._max_editor = QSpinBox()
            for e in (self._min_editor, self._max_editor):
                e.setRange(1900, 2100)
        else:
            self._min_editor = QDoubleSpinBox()
            self._max_editor = QDoubleSpinBox()
            for e in (self._min_editor, self._max_editor):
                e.setRange(0, 10000)
                e.setDecimals(2)
                e.setSuffix(" MB")

        self._min_editor.setPrefix("最小: ")
        self._max_editor.setPrefix("最大: ")

        self._min_editor.valueChanged.connect(self._on_range_changed)
        self._max_editor.valueChanged.connect(self._on_range_changed)

        layout.addWidget(self._min_editor)
        layout.addWidget(self._max_editor)

    def _update_ui(self):
        if len(self._values) >= 2:
            try:
                min_val = float(self._values[0])
                max_val = float(self._values[1])
                self._min_editor.setValue(min_val)
                self._max_editor.setValue(max_val)
            except (ValueError, TypeError):
                pass

    def _on_range_changed(self):
        min_val = self._min_editor.value()
        max_val = self._max_editor.value()
        self._values = [str(min_val), str(max_val)]
        self._notify_changed()

    def get_min_value(self) -> float:
        return self._min_editor.value()

    def get_max_value(self) -> float:
        return self._max_editor.value()


class MultiSelectEditor(BaseValueEditor):
    OPTIONS = {
        "file_format": ["epub", "mobi", "pdf", "azw3", "txt", "doc", "docx"],
        "language": ["中文", "英文", "日文", "韩文", "法文", "德文"],
    }

    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._list_widget.setMaximumHeight(80)

        options = self.OPTIONS.get(self._field, [])
        for opt in options:
            item = QListWidgetItem(opt)
            self._list_widget.addItem(item)

        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list_widget)

    def _update_ui(self):
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item.text() in self._values:
                item.setSelected(True)
            else:
                item.setSelected(False)

    def _on_selection_changed(self):
        self._values = [
            item.text()
            for item in self._list_widget.selectedItems()
        ]
        self._notify_changed()


def create_value_editor(field: str, operator: str) -> BaseValueEditor:
    if operator == "between":
        return RangeValueEditor(field)
    elif operator == "in":
        return MultiSelectEditor(field)
    elif field in ("publish_year", "file_size"):
        return NumericValueEditor(field)
    else:
        return TextValueEditor(field)
