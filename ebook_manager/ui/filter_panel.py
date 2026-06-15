from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QComboBox, QListWidget, QListWidgetItem, QLabel, QGroupBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QDialog, QDialogButtonBox,
    QInputDialog, QMessageBox, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..data_manager import (
    BookDataManager, FilterCondition, SortRule, FilterPreset
)


class FilterItemWidget(QWidget):
    removed = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, condition: FilterCondition, parent=None):
        super().__init__(parent)
        self._condition = condition
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
        self._update_value_editors()

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(remove_btn)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

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

    def _update_value_editors(self):
        while self.value_container.count():
            child = self.value_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        op = self._condition.operator
        field = self._condition.field

        if op == "between":
            self._create_range_editors(field)
        elif op == "in":
            self._create_multi_editor(field)
        else:
            self._create_single_editor(field)

    def _create_single_editor(self, field):
        if field in ("publish_year", "file_size"):
            editor = QDoubleSpinBox() if field == "file_size" else QSpinBox()
            if field == "publish_year":
                editor.setRange(1900, 2100)
            else:
                editor.setRange(0, 10000)
                editor.setDecimals(2)
                editor.setSuffix(" MB")
            if self._condition.values:
                try:
                    editor.setValue(float(self._condition.values[0]))
                except (ValueError, TypeError):
                    pass
            editor.valueChanged.connect(self._on_value_changed)
            self.value_container.addWidget(editor)
        else:
            editor = QLineEdit()
            editor.setPlaceholderText("输入关键词，多个用逗号分隔")
            if self._condition.values:
                editor.setText(", ".join(str(v) for v in self._condition.values))
            editor.textChanged.connect(self._on_text_changed)
            self.value_container.addWidget(editor)

    def _create_range_editors(self, field):
        if field == "publish_year":
            min_editor = QSpinBox()
            max_editor = QSpinBox()
            for e in (min_editor, max_editor):
                e.setRange(1900, 2100)
        else:
            min_editor = QDoubleSpinBox()
            max_editor = QDoubleSpinBox()
            for e in (min_editor, max_editor):
                e.setRange(0, 10000)
                e.setDecimals(2)
                e.setSuffix(" MB")

        min_editor.setPrefix("最小: ")
        max_editor.setPrefix("最大: ")

        if len(self._condition.values) >= 2:
            try:
                min_editor.setValue(float(self._condition.values[0]))
                max_editor.setValue(float(self._condition.values[1]))
            except (ValueError, TypeError):
                pass

        min_editor.valueChanged.connect(self._on_range_changed)
        max_editor.valueChanged.connect(self._on_range_changed)

        self.value_container.addWidget(min_editor)
        self.value_container.addWidget(max_editor)

    def _create_multi_editor(self, field):
        if field == "file_format":
            options = ["epub", "mobi", "pdf", "azw3", "txt", "doc", "docx"]
        elif field == "language":
            options = ["中文", "英文", "日文", "韩文", "法文", "德文"]
        else:
            options = []

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        list_widget.setMaximumHeight(80)
        for opt in options:
            item = QListWidgetItem(opt)
            if opt in self._condition.values:
                item.setSelected(True)
            list_widget.addItem(item)

        if field not in ("file_format", "language"):
            list_widget.addItem("(输入自定义值)")

        list_widget.itemSelectionChanged.connect(self._on_multi_changed)
        self.value_container.addWidget(list_widget)

    def _on_enabled_changed(self, checked):
        self._condition.enabled = checked
        self.changed.emit()

    def _on_field_changed(self, idx):
        self._condition.field = self.field_combo.itemData(idx)
        self._populate_operators()
        self._condition.operator = self.op_combo.itemData(0)
        self._condition.values = []
        self._update_value_editors()
        self.changed.emit()

    def _on_op_changed(self, idx):
        self._condition.operator = self.op_combo.itemData(idx)
        self._condition.values = []
        self._update_value_editors()
        self.changed.emit()

    def _on_value_changed(self, value):
        self._condition.values = [str(value)]
        self.changed.emit()

    def _on_range_changed(self):
        min_val = 0
        max_val = 0
        if self.value_container.count() >= 2:
            min_editor = self.value_container.itemAt(0).widget()
            max_editor = self.value_container.itemAt(1).widget()
            if hasattr(min_editor, "value"):
                min_val = min_editor.value()
            if hasattr(max_editor, "value"):
                max_val = max_editor.value()
        self._condition.values = [str(min_val), str(max_val)]
        self.changed.emit()

    def _on_text_changed(self, text):
        values = [v.strip() for v in text.split(",") if v.strip()]
        self._condition.values = values
        self.changed.emit()

    def _on_multi_changed(self):
        list_widget = self.value_container.itemAt(0).widget()
        if isinstance(list_widget, QListWidget):
            values = [item.text() for item in list_widget.selectedItems() if item.text() != "(输入自定义值)"]
            self._condition.values = values
            self.changed.emit()

    def get_condition(self) -> FilterCondition:
        return self._condition


class SortRuleWidget(QWidget):
    removed = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, rule: SortRule, parent=None):
        super().__init__(parent)
        self._rule = rule
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        self.field_combo = QComboBox()
        self.field_combo.addItem("书名", "title")
        self.field_combo.addItem("作者", "author")
        self.field_combo.addItem("出版社", "publisher")
        self.field_combo.addItem("出版年份", "publish_year")
        self.field_combo.addItem("格式", "file_format")
        self.field_combo.addItem("大小", "file_size")
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


class FilterPanel(QWidget):
    filter_changed = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, data_manager: BookDataManager, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._filter_items: list[FilterItemWidget] = []
        self._sort_items: list[SortRuleWidget] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        title_label = QLabel("🔍 高级筛选")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)

        preset_group = QGroupBox("预设方案")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(4)

        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self._refresh_preset_combo()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.preset_combo, 1)

        load_btn = QPushButton("加载")
        load_btn.clicked.connect(self._load_selected_preset)
        preset_row.addWidget(load_btn)

        save_btn = QPushButton("保存当前")
        save_btn.clicked.connect(self._save_current_as_preset)
        preset_row.addWidget(save_btn)

        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._delete_selected_preset)
        preset_row.addWidget(delete_btn)

        preset_layout.addLayout(preset_row)

        quick_presets_row = QHBoxLayout()
        for preset in self._data_manager.get_presets()[:4]:
            btn = QPushButton(preset.name)
            btn.clicked.connect(lambda checked, name=preset.name: self._quick_load_preset(name))
            quick_presets_row.addWidget(btn)
        preset_layout.addLayout(quick_presets_row)

        scroll_layout.addWidget(preset_group)

        filter_group = QGroupBox("筛选条件")
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(4)

        self.filter_list_layout = QVBoxLayout()
        self.filter_list_layout.setSpacing(2)
        filter_layout.addLayout(self.filter_list_layout)

        add_filter_btn = QPushButton("+ 添加筛选条件")
        add_filter_btn.clicked.connect(self._add_filter_condition)
        filter_layout.addWidget(add_filter_btn)

        filter_buttons_row = QHBoxLayout()
        clear_btn = QPushButton("清空条件")
        clear_btn.clicked.connect(self._clear_conditions)
        filter_buttons_row.addWidget(clear_btn)

        apply_btn = QPushButton("应用筛选")
        apply_btn.clicked.connect(self._apply_filter)
        filter_buttons_row.addWidget(apply_btn)
        filter_layout.addLayout(filter_buttons_row)

        scroll_layout.addWidget(filter_group)

        sort_group = QGroupBox("排序规则")
        sort_layout = QVBoxLayout(sort_group)
        sort_layout.setSpacing(4)

        self.sort_list_layout = QVBoxLayout()
        self.sort_list_layout.setSpacing(2)
        sort_layout.addLayout(self.sort_list_layout)

        add_sort_btn = QPushButton("+ 添加排序规则")
        add_sort_btn.clicked.connect(self._add_sort_rule)
        sort_layout.addWidget(add_sort_btn)

        clear_sort_btn = QPushButton("清空排序")
        clear_sort_btn.clicked.connect(self._clear_sort)
        sort_layout.addWidget(clear_sort_btn)

        scroll_layout.addWidget(sort_group)

        export_group = QGroupBox("导出")
        export_layout = QVBoxLayout(export_group)

        export_btn = QPushButton("📊 导出筛选结果到Excel")
        export_btn.clicked.connect(self.export_requested.emit)
        export_layout.addWidget(export_btn)

        scroll_layout.addWidget(export_group)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        self.setMinimumWidth(350)
        self.setMaximumWidth(420)

    def _refresh_preset_combo(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("选择预设方案...", "")
        for preset in self._data_manager.get_presets():
            self.preset_combo.addItem(preset.name, preset.name)
        self.preset_combo.blockSignals(False)

    def _on_preset_selected(self, idx):
        pass

    def _quick_load_preset(self, name: str):
        self._data_manager.load_preset(name)
        self._rebuild_ui_from_manager()
        self.filter_changed.emit()

    def _load_selected_preset(self):
        name = self.preset_combo.currentData()
        if name:
            self._quick_load_preset(name)

    def _save_current_as_preset(self):
        name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称:")
        if ok and name:
            conditions = [item.get_condition() for item in self._filter_items]
            sort_rules = [item.get_rule() for item in self._sort_items]
            preset = FilterPreset(name=name, conditions=conditions, sort_rules=sort_rules)
            self._data_manager.add_preset(preset)
            self._refresh_preset_combo()
            QMessageBox.information(self, "成功", f"预设方案「{name}」已保存")

    def _delete_selected_preset(self):
        name = self.preset_combo.currentData()
        if name:
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除预设方案「{name}」吗？"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._data_manager.delete_preset(name)
                self._refresh_preset_combo()

    def _add_filter_condition(self):
        condition = FilterCondition(field="title", operator="contains", values=[])
        self._add_filter_item(condition)

    def _add_filter_item(self, condition: FilterCondition):
        item = FilterItemWidget(condition)
        item.removed.connect(self._remove_filter_item)
        item.changed.connect(self._on_filter_item_changed)
        self._filter_items.append(item)
        self.filter_list_layout.addWidget(item)

    def _remove_filter_item(self, item: FilterItemWidget):
        self._filter_items.remove(item)
        item.deleteLater()
        self._on_filter_item_changed()

    def _on_filter_item_changed(self):
        conditions = [item.get_condition() for item in self._filter_items]
        self._data_manager.set_conditions(conditions)

    def _clear_conditions(self):
        for item in self._filter_items:
            item.deleteLater()
        self._filter_items.clear()
        self._data_manager.set_conditions([])

    def _add_sort_rule(self):
        rule = SortRule(field="title", order="asc", pinyin=False)
        self._add_sort_item(rule)

    def _add_sort_item(self, rule: SortRule):
        item = SortRuleWidget(rule)
        item.removed.connect(self._remove_sort_item)
        item.changed.connect(self._on_sort_item_changed)
        self._sort_items.append(item)
        self.sort_list_layout.addWidget(item)

    def _remove_sort_item(self, item: SortRuleWidget):
        self._sort_items.remove(item)
        item.deleteLater()
        self._on_sort_item_changed()

    def _on_sort_item_changed(self):
        rules = [item.get_rule() for item in self._sort_items]
        self._data_manager.set_sort_rules(rules)

    def _clear_sort(self):
        for item in self._sort_items:
            item.deleteLater()
        self._sort_items.clear()
        self._data_manager.set_sort_rules([])

    def _apply_filter(self):
        self.filter_changed.emit()

    def _rebuild_ui_from_manager(self):
        for item in self._filter_items:
            item.deleteLater()
        self._filter_items.clear()

        for item in self._sort_items:
            item.deleteLater()
        self._sort_items.clear()

        for condition in self._data_manager.get_conditions():
            self._add_filter_item(condition)

        for rule in self._data_manager.get_sort_rules():
            self._add_sort_item(rule)
