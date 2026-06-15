from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QCheckBox, QDialogButtonBox, QFileDialog,
    QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from ..data_manager import BookDataManager, FilterCondition


class ExportDialog(QDialog):
    EXPORT_FIELDS = [
        ("title", "书名", True),
        ("author", "作者", True),
        ("publisher", "出版社", True),
        ("publish_date", "出版日期", True),
        ("isbn", "ISBN", True),
        ("language", "语言", True),
        ("file_format", "文件格式", True),
        ("file_size", "文件大小(MB)", True),
        ("tags", "标签", True),
        ("description", "简介", False),
        ("file_path", "文件路径", True),
        ("cover_path", "封面路径", False),
    ]

    def __init__(self, data_manager: BookDataManager, extra_conditions: Optional[list[FilterCondition]] = None, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._extra_conditions = extra_conditions
        self._selected_fields: list[str] = []
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("导出筛选结果")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        info_label = QLabel(
            f"将导出当前筛选条件下的所有匹配记录。\n"
            f"请选择要包含的字段："
        )
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)

        fields_group = QGroupBox("导出字段")
        fields_layout = QVBoxLayout(fields_group)

        self.fields_list = QListWidget()
        self.fields_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        for field_key, field_name, default_checked in self.EXPORT_FIELDS:
            item = QListWidgetItem(field_name)
            item.setData(Qt.ItemDataRole.UserRole, field_key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if default_checked else Qt.CheckState.Unchecked)
            self.fields_list.addItem(item)

        fields_layout.addWidget(self.fields_list)

        buttons_row = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        buttons_row.addWidget(select_all_btn)

        clear_all_btn = QPushButton("全不选")
        clear_all_btn.clicked.connect(lambda: self._set_all_checked(False))
        buttons_row.addWidget(clear_all_btn)

        buttons_row.addStretch()
        fields_layout.addLayout(buttons_row)

        layout.addWidget(fields_group)

        self.include_header_cb = QCheckBox("包含表头行")
        self.include_header_cb.setChecked(True)
        layout.addWidget(self.include_header_cb)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("导出...")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _set_all_checked(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.fields_list.count()):
            item = self.fields_list.item(i)
            item.setCheckState(state)

    def _on_accept(self):
        selected = []
        for i in range(self.fields_list.count()):
            item = self.fields_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))

        if not selected:
            QMessageBox.warning(self, "提示", "请至少选择一个导出字段")
            return

        self._selected_fields = selected
        self._show_save_dialog()

    def _show_save_dialog(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出Excel文件",
            "筛选结果.xlsx",
            "Excel文件 (*.xlsx)"
        )

        if not filepath:
            return

        if not filepath.endswith(".xlsx"):
            filepath += ".xlsx"

        try:
            count = self._data_manager.export_to_excel(
                filepath,
                columns=self._selected_fields,
                extra_conditions=self._extra_conditions
            )
            QMessageBox.information(
                self,
                "导出成功",
                f"成功导出 {count} 条记录到：\n{filepath}"
            )
            self.accept()
        except ImportError as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出Excel需要安装以下依赖库：\n\n"
                f"• pandas (用于数据处理)\n"
                f"• openpyxl (用于Excel生成)\n\n"
                f"请运行: pip install pandas openpyxl\n\n"
                f"错误信息: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中发生错误：\n{str(e)}"
            )

    def get_selected_fields(self) -> list[str]:
        return self._selected_fields
