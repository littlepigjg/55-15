"""
测试文件拆分后的模块导入
验证每个编辑器类都可以独立导入
"""
import sys
import os


def check_pyqt6():
    try:
        from PyQt6.QtWidgets import QApplication
        return True
    except ImportError:
        return False


def test_core_imports():
    """测试不依赖PyQt6的核心模块"""
    print("=" * 60)
    print("测试1: 核心模块导入（不依赖UI）")
    print("=" * 60)

    modules = [
        ("ebook_manager.data_manager", ["BookDataManager", "FilterCondition", "SortRule", "FilterPreset", "FilterResult"]),
        ("ebook_manager.models", ["BookMeta"]),
    ]

    all_ok = True
    for module_name, symbols in modules:
        try:
            module = __import__(module_name, fromlist=symbols)
            ok = True
            missing = []
            for sym in symbols:
                if not hasattr(module, sym):
                    ok = False
                    missing.append(sym)
            if ok:
                print(f"  ✅ {module_name}")
                for sym in symbols:
                    print(f"       - {sym}")
            else:
                print(f"  ❌ {module_name} 缺少: {missing}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            all_ok = False

    return all_ok


def test_value_editors_subpackage():
    """测试 value_editors 子包每个模块独立导入"""
    print("\n" + "=" * 60)
    print("测试2: value_editors 子包 - 每个文件独立导入")
    print("=" * 60)

    submodules = [
        ("ebook_manager.ui.value_editors.base_editor", ["BaseValueEditor"]),
        ("ebook_manager.ui.value_editors.text_editor", ["TextValueEditor"]),
        ("ebook_manager.ui.value_editors.numeric_editor", ["NumericValueEditor"]),
        ("ebook_manager.ui.value_editors.range_editor", ["RangeValueEditor"]),
        ("ebook_manager.ui.value_editors.multiselect_editor", ["MultiSelectEditor"]),
        ("ebook_manager.ui.value_editors.factory", ["create_value_editor"]),
    ]

    all_ok = True
    for module_name, symbols in submodules:
        try:
            module = __import__(module_name, fromlist=symbols)
            ok = True
            missing = []
            for sym in symbols:
                if not hasattr(module, sym):
                    ok = False
                    missing.append(sym)
            if ok:
                print(f"  ✅ {module_name}")
                for sym in symbols:
                    print(f"       - {sym}")
            else:
                print(f"  ❌ {module_name} 缺少: {missing}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            all_ok = False

    return all_ok


def test_value_editors_package_init():
    """测试 value_editors 包的 __init__.py 聚合导出"""
    print("\n" + "=" * 60)
    print("测试3: value_editors/__init__.py 聚合导出")
    print("=" * 60)

    symbols = [
        "BaseValueEditor",
        "TextValueEditor",
        "NumericValueEditor",
        "RangeValueEditor",
        "MultiSelectEditor",
        "create_value_editor",
    ]

    try:
        from ebook_manager.ui.value_editors import (
            BaseValueEditor, TextValueEditor, NumericValueEditor,
            RangeValueEditor, MultiSelectEditor, create_value_editor
        )
        print("  ✅ from ebook_manager.ui.value_editors import ... 成功")
        for sym in symbols:
            print(f"       - {sym}")
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False


def test_ui_package_init():
    """测试 ui 包的 __init__.py 导出 value_editors 子模块"""
    print("\n" + "=" * 60)
    print("测试4: ui/__init__.py 导出各模块")
    print("=" * 60)

    symbols = [
        "BaseValueEditor",
        "TextValueEditor",
        "NumericValueEditor",
        "RangeValueEditor",
        "MultiSelectEditor",
        "create_value_editor",
        "FilterItemWidget",
        "SortRuleWidget",
        "FilterPanel",
        "base_editor",
        "text_editor",
        "numeric_editor",
        "range_editor",
        "multiselect_editor",
        "factory",
    ]

    try:
        import ebook_manager.ui as ui
        all_ok = True
        for sym in symbols:
            if hasattr(ui, sym):
                print(f"  ✅ ebook_manager.ui.{sym}")
            else:
                print(f"  ❌ ebook_manager.ui.{sym} 缺失")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"  ❌ 导入 ebook_manager.ui 失败: {e}")
        return False


def test_factory_creation():
    """测试工厂函数创建各类型编辑器"""
    print("\n" + "=" * 60)
    print("测试5: create_value_editor 工厂函数创建各类型编辑器")
    print("=" * 60)

    from ebook_manager.ui.value_editors import create_value_editor

    test_cases = [
        ("title", "contains", "TextValueEditor"),
        ("author", "equals", "TextValueEditor"),
        ("tags", "contains", "TextValueEditor"),
        ("file_size", "gte", "NumericValueEditor"),
        ("file_size", "lte", "NumericValueEditor"),
        ("publish_year", "equals", "NumericValueEditor"),
        ("publish_year", "between", "RangeValueEditor"),
        ("file_size", "between", "RangeValueEditor"),
        ("file_format", "in", "MultiSelectEditor"),
        ("language", "in", "MultiSelectEditor"),
    ]

    all_ok = True
    for field, operator, expected_type in test_cases:
        try:
            editor = create_value_editor(field, operator)
            actual_type = type(editor).__name__
            if actual_type == expected_type:
                print(f"  ✅ create_value_editor({field!r}, {operator!r}) -> {actual_type}")
            else:
                print(f"  ❌ create_value_editor({field!r}, {operator!r}) -> {actual_type} (预期: {expected_type})")
                all_ok = False
        except Exception as e:
            print(f"  ❌ create_value_editor({field!r}, {operator!r}) 异常: {e}")
            all_ok = False

    return all_ok


def test_independent_reuse():
    """测试各编辑器可独立复用（不依赖筛选面板上下文）"""
    print("\n" + "=" * 60)
    print("测试6: 各编辑器独立复用能力")
    print("=" * 60)

    from ebook_manager.ui.value_editors import (
        TextValueEditor, NumericValueEditor, RangeValueEditor, MultiSelectEditor
    )

    test_results = []

    # TextValueEditor
    try:
        editor = TextValueEditor("custom_field")
        editor.set_values(["A", "B", "C"])
        values = editor.get_values()
        if values == ["A", "B", "C"]:
            print(f"  ✅ TextValueEditor: set/get 值正常 -> {values}")
            test_results.append(True)
        else:
            print(f"  ❌ TextValueEditor: 预期 ['A', 'B', 'C'], 实际 {values}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ TextValueEditor: {e}")
        test_results.append(False)

    # NumericValueEditor
    try:
        editor = NumericValueEditor("file_size")
        editor.set_values(["99.5"])
        values = editor.get_values()
        if values[0] == "99.5":
            print(f"  ✅ NumericValueEditor: set/get 值正常 -> {values}")
            test_results.append(True)
        else:
            print(f"  ❌ NumericValueEditor: 预期 ['99.5'], 实际 {values}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ NumericValueEditor: {e}")
        test_results.append(False)

    # RangeValueEditor
    try:
        editor = RangeValueEditor("file_size")
        editor.set_values(["10", "50"])
        values = editor.get_values()
        if values[0] == "10.0" and values[1] == "50.0":
            print(f"  ✅ RangeValueEditor: set/get 值正常 -> {values}")
            test_results.append(True)
        else:
            print(f"  ❌ RangeValueEditor: 预期 ['10.0', '50.0'], 实际 {values}")
            test_results.append(False)

        # 测试单边启用
        editor.set_values([None, "100"])
        values = editor.get_values()
        if values[0] is None and values[1] == "100.0":
            print(f"  ✅ RangeValueEditor: 单边启用正常 -> {values}")
            test_results.append(True)
        else:
            print(f"  ❌ RangeValueEditor: 单边启用失败 -> {values}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ RangeValueEditor: {e}")
        test_results.append(False)

    # MultiSelectEditor
    try:
        editor = MultiSelectEditor("file_format")
        options = editor.OPTIONS.get("file_format", [])
        if "epub" in options and "pdf" in options:
            print(f"  ✅ MultiSelectEditor: 预设选项正常 -> {options}")
            test_results.append(True)
        else:
            print(f"  ❌ MultiSelectEditor: 预设选项异常 -> {options}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ MultiSelectEditor: {e}")
        test_results.append(False)

    return all(test_results)


def show_file_structure():
    """展示当前的文件结构"""
    print("\n" + "=" * 60)
    print("文件拆分结构")
    print("=" * 60)

    base = os.path.join(os.path.dirname(__file__), "ebook_manager", "ui", "value_editors")
    if os.path.exists(base):
        for f in sorted(os.listdir(base)):
            path = os.path.join(base, f)
            if os.path.isdir(path):
                continue
            size = os.path.getsize(path)
            lines = 0
            with open(path, encoding="utf-8") as fp:
                lines = len(fp.readlines())
            print(f"  📄 value_editors/{f:25} {size:>5} 字节, {lines:>3} 行")

    print()
    other_files = [
        "ebook_manager/ui/filter_item_widget.py",
        "ebook_manager/ui/sort_rule_widget.py",
        "ebook_manager/ui/filter_panel.py",
        "ebook_manager/data_manager.py",
    ]
    for f in other_files:
        path = os.path.join(os.path.dirname(__file__), f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            with open(path, encoding="utf-8") as fp:
                lines = len(fp.readlines())
            print(f"  📄 {f:45} {size:>5} 字节, {lines:>3} 行")


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("模块拆分与导入测试")
    print("=" * 60)

    pyqt_ok = check_pyqt6()
    if not pyqt_ok:
        print("\n⚠️  PyQt6 不可用，仅测试不依赖UI的部分")

    results = []

    results.append(("核心模块", test_core_imports()))

    if pyqt_ok:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        results.append(("value_editors子包", test_value_editors_subpackage()))
        results.append(("value_editors聚合导出", test_value_editors_package_init()))
        results.append(("ui包导出", test_ui_package_init()))
        results.append(("工厂函数", test_factory_creation()))
        results.append(("独立复用", test_independent_reuse()))

    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    all_passed = True
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {name:25} {status}")
        if not ok:
            all_passed = False

    show_file_structure()

    if all_passed:
        print("\n🎉 全部通过！文件拆分完整，模块可独立导入复用。")
    else:
        print("\n⚠️  部分测试未通过，请检查上面的详细输出。")
        sys.exit(1)
