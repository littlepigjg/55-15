from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..data_manager import BookDataManager, FilterCondition
from .value_editors import create_value_editor, BaseValueEditor


class FilterItemWidget(QWidget):
    removed = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, condition: FilterCondition, parent=None):
        super().__init__(parent)
        self._condition = condition
        self._value_editor: BaseValueEditor | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        self.enabled_cb = QCheckBox()
        self.enabled_cb.setChecked(self._condition.enabled)
        self.enabled_cb.toggled.connect(self._on_enabled_changed)
        layout.addWidget(self.enabled_cb)

        self.field_combo = QComboBox()
        for field_key, field_name in BookDataManager.FILTER_FIELDS.items():
            self.field_combo.addItem(field_name, field_key)
        idx = self.field_combo.findData(self._condition.field)
        if idx >= 0:
            self.field_combo.setCurrentIndex(idx)
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)
        self.field_combo.setMinimumWidth(100)
        layout.addWidget(self.field_combo)

        self.op_combo = QComboBox()
        self._populate_operators()
        idx = self.op_combo.findData(self._condition.operator)
        if idx >= 0:
            self.op_combo.setCurrentIndex(idx)
        self.op_combo.currentIndexChanged.connect(self._on_op_changed)
        self.op_combo.setMinimumWidth(100)
        layout.addWidget(self.op_combo)

        self.value_container = QHBoxLayout()
        self.value_container.setSpacing(4)
        layout.addLayout(self.value_container, 1)
        self._update_value_editor()

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(remove_btn)

        self.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Preferred
        )

    def _populate_operators(self):
        self.op_combo.clear()
        field = self._condition.field

        if field in ("publish_year", "file_size"):
            operators = [
                ("等于", "equals"),
                ("不等于", "not_equals"),
                ("大于", "gt"),
                ("大于等于", "gte"),
                ("小于", "lt"),
                ("小于等于", "lte"),
                ("在范围内", "between"),
            ]
        elif field in ("file_format", "language"):
            operators = [
                ("等于", "equals"),
                ("不等于", "not_equals"),
                ("多选匹配", "in"),
            ]
        else:
            operators = [
                ("包含", "contains"),
                ("不包含", "not_contains"),
                ("等于", "equals"),
                ("不等于", "not_equals"),
                ("开头是", "starts_with"),
                ("结尾是", "ends_with"),
                ("正则匹配", "regex"),
            ]

        for name, op in operators:
            self.op_combo.addItem(name, op)

    def _update_value_editor(self):
        while self.value_container.count():
            child = self.value_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._value_editor = create_value_editor(
            self._condition.field,
            self._condition.operator
        )
        if self._value_editor:
            self._value_editor.set_values(self._condition.values)
            self._value_editor.value_changed.connect(self._on_value_changed)
            self.value_container.addWidget(self._value_editor)

    def _on_enabled_changed(self, checked):
        self._condition.enabled = checked
        self.changed.emit()

    def _on_field_changed(self, idx):
        self._condition.field = self.field_combo.itemData(idx)
        self._populate_operators()
        self._condition.operator = self.op_combo.itemData(0)
        self._condition.values = []
        self._update_value_editor()
        self.changed.emit()

    def _on_op_changed(self, idx):
        self._condition.operator = self.op_combo.itemData(idx)
        self._condition.values = []
        self._update_value_editor()
        self.changed.emit()

    def _on_value_changed(self, values: list):
        self._condition.values = values
        self.changed.emit()

    def get_condition(self) -> FilterCondition:
        return self._condition
