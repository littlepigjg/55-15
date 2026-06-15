from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal

from ..data_manager import SortRule


class SortRuleWidget(QWidget):
    removed = pyqtSignal(object)
    changed = pyqtSignal()

    SORT_FIELDS = [
        ("书名", "title"),
        ("作者", "author"),
        ("出版社", "publisher"),
        ("出版年份", "publish_year"),
        ("格式", "file_format"),
        ("大小", "file_size"),
    ]

    def __init__(self, rule: SortRule, parent=None):
        super().__init__(parent)
        self._rule = rule
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        self.field_combo = QComboBox()
        for name, key in self.SORT_FIELDS:
            self.field_combo.addItem(name, key)
        idx = self.field_combo.findData(self._rule.field)
        if idx >= 0:
            self.field_combo.setCurrentIndex(idx)
        self.field_combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.field_combo)

        self.order_combo = QComboBox()
        self.order_combo.addItem("升序", "asc")
        self.order_combo.addItem("降序", "desc")
        idx = self.order_combo.findData(self._rule.order)
        if idx >= 0:
            self.order_combo.setCurrentIndex(idx)
        self.order_combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.order_combo)

        self.pinyin_cb = QCheckBox("拼音排序")
        self.pinyin_cb.setChecked(self._rule.pinyin)
        self.pinyin_cb.toggled.connect(self._on_changed)
        layout.addWidget(self.pinyin_cb)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(remove_btn)

    def _on_changed(self):
        self._rule.field = self.field_combo.currentData()
        self._rule.order = self.order_combo.currentData()
        self._rule.pinyin = self.pinyin_cb.isChecked()
        self.changed.emit()

    def get_rule(self) -> SortRule:
        return self._rule
