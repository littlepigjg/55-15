from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem

from .base_editor import BaseValueEditor


class MultiSelectEditor(BaseValueEditor):
    OPTIONS = {
        "file_format": ["epub", "mobi", "pdf", "azw3", "txt", "doc", "docx"],
        "language": ["中文", "英文", "日文", "韩文", "法文", "德文"],
    }

    def __init__(self, field: str, parent=None):
        super().__init__(field, parent)
        self._list_widget = None
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

    def get_selected_options(self) -> list[str]:
        return [item.text() for item in self._list_widget.selectedItems()]
