from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QAbstractItemView, QPushButton, QLineEdit,
    QComboBox, QLabel, QSpinBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..models import BookMeta
from ..data_manager import FilterResult


class PaginatedBookTable(QWidget):
    selection_changed = pyqtSignal(list)
    edit_requested = pyqtSignal(list)
    convert_requested = pyqtSignal(list)
    search_meta_requested = pyqtSignal(list)
    page_changed = pyqtSignal(int)
    page_size_changed = pyqtSignal(int)

    COLUMNS = [
        ("选择", 40),
        ("书名", 200),
        ("作者", 150),
        ("出版社", 150),
        ("出版日期", 100),
        ("ISBN", 130),
        ("语言", 60),
        ("格式", 60),
        ("大小", 80),
        ("路径", 250),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_books: list[BookMeta] = []
        self._page_books: list[BookMeta] = []
        self._page = 1
        self._page_size = 100
        self._total_pages = 1
        self._total_count = 0
        self._filtered_count = 0
        self._elapsed_ms = 0.0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)
        toolbar.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        toolbar.addWidget(self.deselect_all_btn)

        toolbar.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("快速搜索书名/作者...")
        self.search_edit.setFixedWidth(250)
        self.search_edit.textChanged.connect(self._on_quick_search)
        toolbar.addWidget(self.search_edit)

        self.format_filter = QComboBox()
        self.format_filter.addItem("全部格式")
        self.format_filter.addItem("EPUB")
        self.format_filter.addItem("MOBI")
        self.format_filter.addItem("PDF")
        toolbar.addWidget(self.format_filter)

        layout.addLayout(toolbar)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(
            "background: #f0f7ff; padding: 6px 12px; border-radius: 4px; "
            "color: #333; font-weight: 500;"
        )
        layout.addWidget(self.stats_label)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemChanged.connect(self._on_item_changed)

        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(self.COLUMNS):
            header.setMinimumSectionSize(30)
            if i == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, width)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.table.setColumnWidth(i, width)

        header.setStretchLastSection(True)
        self.table.setSortingEnabled(False)
        layout.addWidget(self.table, 1)

        pagination_bar = QHBoxLayout()
        pagination_bar.setContentsMargins(8, 4, 8, 4)

        self.first_btn = QPushButton("⏮")
        self.first_btn.setFixedWidth(40)
        self.first_btn.clicked.connect(lambda: self._go_to_page(1))
        pagination_bar.addWidget(self.first_btn)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(lambda: self._go_to_page(self._page - 1))
        pagination_bar.addWidget(self.prev_btn)

        pagination_bar.addStretch()

        page_label = QLabel("第")
        pagination_bar.addWidget(page_label)

        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.setFixedWidth(70)
        self.page_spin.valueChanged.connect(self._on_page_spin_changed)
        pagination_bar.addWidget(self.page_spin)

        self.total_pages_label = QLabel("/ 1 页")
        pagination_bar.addWidget(self.total_pages_label)

        pagination_bar.addSpacing(20)

        page_size_label = QLabel("每页显示:")
        pagination_bar.addWidget(page_size_label)

        self.page_size_combo = QComboBox()
        for size in [20, 50, 100, 200, 500, 1000]:
            self.page_size_combo.addItem(str(size), size)
        self.page_size_combo.setCurrentIndex(2)
        self.page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        pagination_bar.addWidget(self.page_size_combo)

        pagination_bar.addSpacing(20)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(lambda: self._go_to_page(self._page + 1))
        pagination_bar.addWidget(self.next_btn)

        self.last_btn = QPushButton("⏭")
        self.last_btn.setFixedWidth(40)
        self.last_btn.clicked.connect(lambda: self._go_to_page(self._total_pages))
        pagination_bar.addWidget(self.last_btn)

        pagination_bar.addStretch()

        self.page_info_label = QLabel("")
        self.page_info_label.setStyleSheet("color: #666;")
        pagination_bar.addWidget(self.page_info_label)

        layout.addLayout(pagination_bar)

    def load_books(self, books: list[BookMeta]):
        self._all_books = books
        self._page = 1
        self._update_stats(self._total_count, len(books), 0)

    def update_from_result(self, result: FilterResult):
        self._page_books = result.books
        self._page = result.page
        self._page_size = result.page_size
        self._total_pages = result.total_pages
        self._total_count = result.total_count
        self._filtered_count = result.filtered_count
        self._elapsed_ms = result.elapsed_ms

        self._populate_table(result.books)
        self._update_pagination_controls()
        self._update_stats(result.total_count, result.filtered_count, result.elapsed_ms)

    def _update_stats(self, total: int, filtered: int, elapsed_ms: float):
        if filtered == total:
            stats_text = f"📚 总共 {total} 本书籍"
        else:
            stats_text = f"📚 筛选结果: {filtered} / {total} 本"

        if elapsed_ms > 0:
            stats_text += f"  |  ⚡ 耗时: {elapsed_ms:.1f} ms"

        self.stats_label.setText(stats_text)

    def _update_pagination_controls(self):
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, max(1, self._total_pages))
        self.page_spin.setValue(self._page)
        self.page_spin.blockSignals(False)

        self.total_pages_label.setText(f"/ {self._total_pages} 页")

        has_prev = self._page > 1
        has_next = self._page < self._total_pages

        self.first_btn.setEnabled(has_prev)
        self.prev_btn.setEnabled(has_prev)
        self.next_btn.setEnabled(has_next)
        self.last_btn.setEnabled(has_next)

        start_idx = (self._page - 1) * self._page_size + 1
        end_idx = min(self._page * self._page_size, self._filtered_count)
        if self._filtered_count > 0:
            self.page_info_label.setText(f"显示 {start_idx}-{end_idx} / 共 {self._filtered_count} 条")
        else:
            self.page_info_label.setText("无数据")

    def _populate_table(self, books: list[BookMeta]):
        self.table.blockSignals(True)
        self.table.setRowCount(len(books))

        for row, book in enumerate(books):
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, row)
            self.table.setItem(row, 0, check_item)

            self.table.setItem(row, 1, QTableWidgetItem(book.title))
            self.table.setItem(row, 2, QTableWidgetItem(book.author))
            self.table.setItem(row, 3, QTableWidgetItem(book.publisher))
            self.table.setItem(row, 4, QTableWidgetItem(book.publish_date))
            self.table.setItem(row, 5, QTableWidgetItem(book.isbn))
            self.table.setItem(row, 6, QTableWidgetItem(book.language))
            self.table.setItem(row, 7, QTableWidgetItem(book.file_format.upper()))

            size_item = QTableWidgetItem(BookMeta.format_size(book.file_size))
            size_item.setData(Qt.ItemDataRole.UserRole, book.file_size)
            self.table.setItem(row, 8, size_item)

            self.table.setItem(row, 9, QTableWidgetItem(book.file_path))

        self.table.blockSignals(False)

    def _go_to_page(self, page: int):
        if 1 <= page <= self._total_pages and page != self._page:
            self._page = page
            self.page_spin.setValue(page)
            self.page_changed.emit(page)

    def _on_page_spin_changed(self, value: int):
        self._go_to_page(value)

    def _on_page_size_changed(self, idx: int):
        self._page_size = self.page_size_combo.itemData(idx)
        self._page = 1
        self.page_size_changed.emit(self._page_size)

    def get_current_page(self) -> int:
        return self._page

    def get_page_size(self) -> int:
        return self._page_size

    def get_selected_books(self) -> list:
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                idx = item.data(Qt.ItemDataRole.UserRole)
                if 0 <= idx < len(self._page_books):
                    selected.append(self._page_books[idx])
        return selected

    def get_all_filtered_books(self) -> list:
        return self._all_books

    def refresh_row(self, row_idx: int, book: BookMeta):
        if 0 <= row_idx < len(self._page_books):
            self._page_books[row_idx] = book
            self.table.blockSignals(True)
            self.table.item(row_idx, 1).setText(book.title)
            self.table.item(row_idx, 2).setText(book.author)
            self.table.item(row_idx, 3).setText(book.publisher)
            self.table.item(row_idx, 4).setText(book.publish_date)
            self.table.item(row_idx, 5).setText(book.isbn)
            self.table.item(row_idx, 6).setText(book.language)
            self.table.blockSignals(False)

    def _select_all(self):
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(Qt.CheckState.Checked)
        self.table.blockSignals(False)
        self._notify_selection()

    def _deselect_all(self):
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(Qt.CheckState.Unchecked)
        self.table.blockSignals(False)
        self._notify_selection()

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            self._notify_selection()

    def _notify_selection(self):
        self.selection_changed.emit(self.get_selected_books())

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ 编辑元数据")
        search_action = menu.addAction("🔍 在线搜索元数据")
        convert_action = menu.addAction("🔄 转换格式")
        menu.addSeparator()
        open_action = menu.addAction("📂 打开文件位置")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        selected = self.get_selected_books()
        if not selected:
            return
        if action == edit_action:
            self.edit_requested.emit(selected)
        elif action == search_action:
            self.search_meta_requested.emit(selected)
        elif action == convert_action:
            self.convert_requested.emit(selected)
        elif action == open_action:
            import os
            import subprocess
            path = selected[0].file_path
            if os.path.exists(path):
                subprocess.Popen(f'explorer /select,"{path}"')

    def _on_quick_search(self):
        pass

    def get_filtered_count(self) -> int:
        return self._filtered_count
