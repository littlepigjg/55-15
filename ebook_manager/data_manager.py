from __future__ import annotations

import re
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from collections import OrderedDict

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from pypinyin import pinyin, Style
    PINYIN_AVAILABLE = True
except ImportError:
    PINYIN_AVAILABLE = False

from .models import BookMeta


@dataclass
class FilterCondition:
    field: str
    operator: str
    values: list
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "operator": self.operator,
            "values": self.values,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FilterCondition":
        return cls(
            field=d.get("field", ""),
            operator=d.get("operator", ""),
            values=d.get("values", []),
            enabled=d.get("enabled", True),
        )


@dataclass
class SortRule:
    field: str
    order: str = "asc"
    pinyin: bool = False

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "order": self.order,
            "pinyin": self.pinyin,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SortRule":
        return cls(
            field=d.get("field", ""),
            order=d.get("order", "asc"),
            pinyin=d.get("pinyin", False),
        )


@dataclass
class FilterPreset:
    name: str
    conditions: list[FilterCondition] = field(default_factory=list)
    sort_rules: list[SortRule] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions],
            "sort_rules": [s.to_dict() for s in self.sort_rules],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FilterPreset":
        return cls(
            name=d.get("name", ""),
            conditions=[FilterCondition.from_dict(c) for c in d.get("conditions", [])],
            sort_rules=[SortRule.from_dict(s) for s in d.get("sort_rules", [])],
        )


@dataclass
class FilterResult:
    books: list[BookMeta]
    total_count: int
    filtered_count: int
    elapsed_ms: float
    page: int = 1
    page_size: int = 100
    total_pages: int = 1


class BookDataManager:
    FILTER_FIELDS = OrderedDict([
        ("title", "书名"),
        ("author", "作者"),
        ("publisher", "出版社"),
        ("publish_year", "出版年份"),
        ("isbn", "ISBN"),
        ("language", "语言"),
        ("file_format", "文件格式"),
        ("file_size", "文件大小(MB)"),
        ("tags", "标签"),
        ("description", "简介"),
    ])

    OPERATORS = {
        "contains": "包含",
        "not_contains": "不包含",
        "equals": "等于",
        "not_equals": "不等于",
        "starts_with": "开头是",
        "ends_with": "结尾是",
        "gt": "大于",
        "gte": "大于等于",
        "lt": "小于",
        "lte": "小于等于",
        "between": "在范围内",
        "in": "多选匹配",
        "regex": "正则匹配",
    }

    def __init__(self):
        self._books: list[BookMeta] = []
        self._df = None
        self._filter_conditions: list[FilterCondition] = []
        self._sort_rules: list[SortRule] = []
        self._presets: list[FilterPreset] = []
        self._pinyin_cache: dict[str, str] = {}

        self._init_default_presets()

    def _init_default_presets(self):
        self._presets = [
            FilterPreset(
                name="近期新书",
                conditions=[
                    FilterCondition(field="publish_year", operator="gte", values=["2020"]),
                ],
                sort_rules=[
                    SortRule(field="publish_year", order="desc"),
                ],
            ),
            FilterPreset(
                name="大文件清理",
                conditions=[
                    FilterCondition(field="file_size", operator="gte", values=["10"]),
                ],
                sort_rules=[
                    SortRule(field="file_size", order="desc"),
                ],
            ),
            FilterPreset(
                name="Python编程书",
                conditions=[
                    FilterCondition(field="title", operator="contains", values=["Python", "python"]),
                    FilterCondition(field="tags", operator="contains", values=["编程", "程序设计"]),
                    FilterCondition(field="publish_year", operator="gte", values=["2020"]),
                ],
                sort_rules=[
                    SortRule(field="publish_year", order="desc"),
                ],
            ),
            FilterPreset(
                name="EPUB/PDF格式",
                conditions=[
                    FilterCondition(field="file_format", operator="in", values=["epub", "pdf"]),
                ],
                sort_rules=[],
            ),
        ]

    def load_books(self, books: list[BookMeta]):
        self._books = books
        self._build_dataframe()

    def _build_dataframe(self):
        if not self._books:
            self._df = None
            return

        data = []
        for book in self._books:
            publish_year = ""
            if book.publish_date:
                match = re.search(r"(\d{4})", book.publish_date)
                if match:
                    publish_year = match.group(1)

            data.append({
                "title": book.title,
                "author": book.author,
                "publisher": book.publisher,
                "publish_date": book.publish_date,
                "publish_year": publish_year,
                "isbn": book.isbn,
                "language": book.language,
                "file_format": book.file_format.lower() if book.file_format else "",
                "file_size": round(book.file_size / (1024 * 1024), 2),
                "tags": ",".join(book.tags) if book.tags else "",
                "description": book.description,
                "file_path": book.file_path,
                "_book_ref": book,
            })

        if PANDAS_AVAILABLE:
            self._df = pd.DataFrame(data)
        else:
            self._df = data

    def get_all_books(self) -> list[BookMeta]:
        return self._books

    def set_conditions(self, conditions: list[FilterCondition]):
        self._filter_conditions = conditions

    def get_conditions(self) -> list[FilterCondition]:
        return self._filter_conditions

    def set_sort_rules(self, rules: list[SortRule]):
        self._sort_rules = rules

    def get_sort_rules(self) -> list[SortRule]:
        return self._sort_rules

    def get_presets(self) -> list[FilterPreset]:
        return self._presets

    def add_preset(self, preset: FilterPreset):
        self._presets.append(preset)
        self._save_presets()

    def delete_preset(self, name: str):
        self._presets = [p for p in self._presets if p.name != name]
        self._save_presets()

    def load_preset(self, name: str) -> Optional[FilterPreset]:
        for preset in self._presets:
            if preset.name == name:
                self._filter_conditions = list(preset.conditions)
                self._sort_rules = list(preset.sort_rules)
                return preset
        return None

    def _save_presets(self):
        try:
            preset_file = Path.home() / ".ebook_manager" / "presets.json"
            preset_file.parent.mkdir(exist_ok=True)
            data = [p.to_dict() for p in self._presets]
            preset_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def load_presets_from_file(self):
        try:
            preset_file = Path.home() / ".ebook_manager" / "presets.json"
            if preset_file.exists():
                data = json.loads(preset_file.read_text(encoding="utf-8"))
                self._presets = [FilterPreset.from_dict(d) for d in data]
        except Exception:
            pass

    def _get_pinyin(self, text: str) -> str:
        if not text:
            return ""
        if text in self._pinyin_cache:
            return self._pinyin_cache[text]

        if PINYIN_AVAILABLE:
            result = "".join([item[0] for item in pinyin(text, style=Style.NORMAL)])
        else:
            result = text.lower()

        self._pinyin_cache[text] = result
        return result

    def apply_filters(self, page: int = 1, page_size: int = 100, extra_conditions: Optional[list[FilterCondition]] = None) -> FilterResult:
        start_time = time.time()
        total_count = len(self._books)

        if self._df is None:
            return FilterResult(
                books=[],
                total_count=0,
                filtered_count=0,
                elapsed_ms=0,
                page=1,
                page_size=page_size,
                total_pages=1,
            )

        filtered = self._apply_filters_internal(extra_conditions)
        filtered = self._apply_sort_internal(filtered)
        filtered_count = len(filtered)

        total_pages = max(1, (filtered_count + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, filtered_count)

        if PANDAS_AVAILABLE:
            page_books = [row["_book_ref"] for _, row in filtered.iloc[start_idx:end_idx].iterrows()]
        else:
            page_books = [item["_book_ref"] for item in filtered[start_idx:end_idx]]

        elapsed_ms = (time.time() - start_time) * 1000

        return FilterResult(
            books=page_books,
            total_count=total_count,
            filtered_count=filtered_count,
            elapsed_ms=elapsed_ms,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _apply_filters_internal(self, extra_conditions: Optional[list[FilterCondition]] = None):
        enabled_conditions = [c for c in self._filter_conditions if c.enabled and c.values]

        if extra_conditions:
            enabled_conditions = enabled_conditions + [c for c in extra_conditions if c.enabled and c.values]

        if not enabled_conditions:
            return self._df.copy() if PANDAS_AVAILABLE else list(self._df)

        if PANDAS_AVAILABLE:
            return self._apply_filters_pandas(enabled_conditions)
        else:
            return self._apply_filters_fallback(enabled_conditions)

    def _apply_filters_pandas(self, conditions: list[FilterCondition]) -> "pd.DataFrame":
        df = self._df.copy()
        mask = pd.Series([True] * len(df))

        for cond in conditions:
            field_mask = self._build_field_mask_pandas(df, cond)
            mask &= field_mask

        return df[mask]

    def _build_field_mask_pandas(self, df: "pd.DataFrame", cond: FilterCondition) -> "pd.Series":
        field = cond.field
        op = cond.operator
        values = cond.values

        if field not in df.columns:
            return pd.Series([True] * len(df))

        series = df[field]

        if op == "contains":
            field_mask = pd.Series([False] * len(df))
            for val in values:
                val_str = str(val).lower()
                field_mask |= series.astype(str).str.lower().str.contains(val_str, na=False)
            return field_mask

        elif op == "not_contains":
            field_mask = pd.Series([True] * len(df))
            for val in values:
                val_str = str(val).lower()
                field_mask &= ~series.astype(str).str.lower().str.contains(val_str, na=False)
            return field_mask

        elif op == "equals":
            val = values[0]
            return series.astype(str).str.lower() == str(val).lower()

        elif op == "not_equals":
            val = values[0]
            return series.astype(str).str.lower() != str(val).lower()

        elif op == "starts_with":
            val = str(values[0]).lower()
            return series.astype(str).str.lower().str.startswith(val, na=False)

        elif op == "ends_with":
            val = str(values[0]).lower()
            return series.astype(str).str.lower().str.endswith(val, na=False)

        elif op in ("gt", "gte", "lt", "lte"):
            try:
                num_val = float(values[0])
                num_series = pd.to_numeric(series, errors="coerce")
                if op == "gt":
                    return num_series > num_val
                elif op == "gte":
                    return num_series >= num_val
                elif op == "lt":
                    return num_series < num_val
                else:
                    return num_series <= num_val
            except (ValueError, TypeError):
                return pd.Series([True] * len(df))

        elif op == "between":
            if len(values) >= 2:
                try:
                    min_val = float(values[0])
                    max_val = float(values[1])
                    num_series = pd.to_numeric(series, errors="coerce")
                    return (num_series >= min_val) & (num_series <= max_val)
                except (ValueError, TypeError):
                    pass
            return pd.Series([True] * len(df))

        elif op == "in":
            vals_lower = [str(v).lower() for v in values]
            return series.astype(str).str.lower().isin(vals_lower)

        elif op == "regex":
            try:
                pattern = re.compile(values[0], re.IGNORECASE)
                return series.astype(str).apply(lambda x: bool(pattern.search(x)))
            except re.error:
                return pd.Series([True] * len(df))

        return pd.Series([True] * len(df))

    def _apply_filters_fallback(self, conditions: list[FilterCondition]) -> list[dict]:
        data = list(self._df)

        for cond in conditions:
            data = [item for item in data if self._match_condition_fallback(item, cond)]

        return data

    def _match_condition_fallback(self, item: dict, cond: FilterCondition) -> bool:
        field = cond.field
        op = cond.operator
        values = cond.values

        if field not in item:
            return True

        field_val = item[field]

        if op == "contains":
            field_str = str(field_val).lower()
            return any(str(v).lower() in field_str for v in values)

        elif op == "not_contains":
            field_str = str(field_val).lower()
            return all(str(v).lower() not in field_str for v in values)

        elif op == "equals":
            return str(field_val).lower() == str(values[0]).lower()

        elif op == "not_equals":
            return str(field_val).lower() != str(values[0]).lower()

        elif op == "starts_with":
            return str(field_val).lower().startswith(str(values[0]).lower())

        elif op == "ends_with":
            return str(field_val).lower().endswith(str(values[0]).lower())

        elif op in ("gt", "gte", "lt", "lte"):
            try:
                num_val = float(values[0])
                num_field = float(field_val)
                if op == "gt":
                    return num_field > num_val
                elif op == "gte":
                    return num_field >= num_val
                elif op == "lt":
                    return num_field < num_val
                else:
                    return num_field <= num_val
            except (ValueError, TypeError):
                return True

        elif op == "between":
            if len(values) >= 2:
                try:
                    min_val = float(values[0])
                    max_val = float(values[1])
                    num_field = float(field_val)
                    return min_val <= num_field <= max_val
                except (ValueError, TypeError):
                    pass
            return True

        elif op == "in":
            vals_lower = [str(v).lower() for v in values]
            return str(field_val).lower() in vals_lower

        elif op == "regex":
            try:
                pattern = re.compile(values[0], re.IGNORECASE)
                return bool(pattern.search(str(field_val)))
            except re.error:
                return True

        return True

    def _apply_sort_internal(self, data):
        if not self._sort_rules:
            return data

        if PANDAS_AVAILABLE:
            return self._apply_sort_pandas(data)
        else:
            return self._apply_sort_fallback(data)

    def _apply_sort_pandas(self, df: "pd.DataFrame") -> "pd.DataFrame":
        sort_keys = []
        ascending = []

        for rule in self._sort_rules:
            if rule.field not in df.columns:
                continue

            if rule.pinyin and PINYIN_AVAILABLE and df[rule.field].dtype == object:
                pinyin_col = f"_pinyin_{rule.field}"
                df[pinyin_col] = df[rule.field].astype(str).apply(self._get_pinyin)
                sort_keys.append(pinyin_col)
            else:
                sort_keys.append(rule.field)

            ascending.append(rule.order == "asc")

        if sort_keys:
            df = df.sort_values(by=sort_keys, ascending=ascending, kind="mergesort")

        return df

    def _apply_sort_fallback(self, data: list[dict]) -> list[dict]:
        sorted_data = list(data)

        for rule in reversed(self._sort_rules):
            reverse = rule.order == "desc"

            if rule.pinyin and PINYIN_AVAILABLE:
                sorted_data.sort(
                    key=lambda x: self._get_pinyin(str(x.get(rule.field, ""))),
                    reverse=reverse,
                )
            else:
                def sort_key(x):
                    val = x.get(rule.field, "")
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return str(val).lower()

                sorted_data.sort(key=sort_key, reverse=reverse)

        return sorted_data

    def export_to_excel(self, filepath: str, columns: Optional[list[str]] = None, extra_conditions: Optional[list[FilterCondition]] = None):
        if self._df is None:
            raise ValueError("没有数据可导出")

        filtered = self._apply_filters_internal(extra_conditions)
        filtered = self._apply_sort_internal(filtered)

        default_columns = [
            ("title", "书名"),
            ("author", "作者"),
            ("publisher", "出版社"),
            ("publish_date", "出版日期"),
            ("isbn", "ISBN"),
            ("language", "语言"),
            ("file_format", "格式"),
            ("file_size", "大小(MB)"),
            ("tags", "标签"),
            ("file_path", "文件路径"),
        ]

        export_cols = columns if columns else [c[0] for c in default_columns]
        col_names = {c[0]: c[1] for c in default_columns}

        if PANDAS_AVAILABLE:
            export_df = filtered[export_cols].copy()
            export_df = export_df.rename(columns=col_names)
            export_df.to_excel(filepath, index=False, engine="openpyxl")
        else:
            try:
                import openpyxl
                from openpyxl.styles import Font, Alignment
            except ImportError:
                raise ImportError("导出Excel需要安装openpyxl库")

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "筛选结果"

            header = [col_names.get(c, c) for c in export_cols]
            ws.append(header)

            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")

            for item in filtered:
                row = [item.get(c, "") for c in export_cols]
                ws.append(row)

            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width

            wb.save(filepath)

        return len(filtered)
