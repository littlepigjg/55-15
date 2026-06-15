from __future__ import annotations

from .base_editor import BaseValueEditor
from .text_editor import TextValueEditor
from .numeric_editor import NumericValueEditor
from .range_editor import RangeValueEditor
from .multiselect_editor import MultiSelectEditor


def create_value_editor(field: str, operator: str) -> BaseValueEditor:
    if operator == "between":
        return RangeValueEditor(field)
    elif operator == "in":
        return MultiSelectEditor(field)
    elif field in ("publish_year", "file_size"):
        return NumericValueEditor(field)
    else:
        return TextValueEditor(field)
