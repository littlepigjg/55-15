from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QGroupBox, QScrollArea, QFrame, QSizePolicy, QInputDialog,
    QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..data_manager import (
    BookDataManager, FilterCondition, SortRule, FilterPreset
)
from .filter_item_widget import FilterItemWidget
from .sort_rule_widget import SortRuleWidget


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

        self._build_preset_group(scroll_layout)
        self._build_filter_group(scroll_layout)
        self._build_sort_group(scroll_layout)
        self._build_export_group(scroll_layout)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        self.setMinimumWidth(350)
        self.setMaximumWidth(420)

    def _build_preset_group(self, parent_layout: QVBoxLayout):
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
            btn.clicked.connect(
                lambda checked, name=preset.name: self._quick_load_preset(name)
            )
            quick_presets_row.addWidget(btn)
        preset_layout.addLayout(quick_presets_row)

        parent_layout.addWidget(preset_group)

    def _build_filter_group(self, parent_layout: QVBoxLayout):
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

        parent_layout.addWidget(filter_group)

    def _build_sort_group(self, parent_layout: QVBoxLayout):
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

        parent_layout.addWidget(sort_group)

    def _build_export_group(self, parent_layout: QVBoxLayout):
        export_group = QGroupBox("导出")
        export_layout = QVBoxLayout(export_group)

        export_btn = QPushButton("📊 导出筛选结果到Excel")
        export_btn.clicked.connect(self.export_requested.emit)
        export_layout.addWidget(export_btn)

        parent_layout.addWidget(export_group)

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
