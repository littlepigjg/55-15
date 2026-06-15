from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLineEdit

from .base_editor import BaseValueEditor


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
