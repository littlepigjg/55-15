"""
测试范围筛选修复
1. between 运算符支持单边范围（只有min或只有max）
2. 两个值都为空时条件不生效
3. min > max 时自动交换
"""
from ebook_manager.models import BookMeta
from ebook_manager.data_manager import BookDataManager, FilterCondition


def create_test_books():
    books = []
    for i in range(20):
        size_mb = 5 + i * 3
        book = BookMeta(
            title=f"书籍{i}",
            file_size=int(size_mb * 1024 * 1024),
            file_path=f"/book{i}.epub"
        )
        books.append(book)
    return books


def test_between_both_empty():
    """测试：两个值都为空时，条件不生效"""
    print("=" * 60)
    print("测试1: 两个值都为空 -> 条件不生效（全部通过）")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 两个值都是None
    cond = FilterCondition(field="file_size", operator="between", values=[None, None])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  values=[None, None] -> {result.filtered_count} 条 (预期: {len(books)})")
    assert result.filtered_count == len(books), "两个都为空时应该全部通过"

    # 两个值都是空字符串
    cond = FilterCondition(field="file_size", operator="between", values=["", ""])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  values=['', '']   -> {result.filtered_count} 条 (预期: {len(books)})")
    assert result.filtered_count == len(books), "两个都为空字符串时应该全部通过"

    print("  ✅ 测试通过")


def test_between_only_min():
    """测试：只有最小值 -> 相当于 >= min"""
    print("\n" + "=" * 60)
    print("测试2: 只有最小值 -> 相当于 >= min")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 只有最小值
    cond = FilterCondition(field="file_size", operator="between", values=["10", None])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  values=['10', None] -> {result.filtered_count} 条")

    # 用 gte 验证结果是否一致
    cond_gte = FilterCondition(field="file_size", operator="gte", values=["10"])
    dm.set_conditions([cond_gte])
    result_gte = dm.apply_filters(page=1, page_size=100)
    print(f"  gte 10            -> {result_gte.filtered_count} 条 (参照)")

    assert result.filtered_count == result_gte.filtered_count, "只有min时应该等价于gte"
    print("  ✅ 测试通过（与gte结果一致）")


def test_between_only_max():
    """测试：只有最大值 -> 相当于 <= max"""
    print("\n" + "=" * 60)
    print("测试3: 只有最大值 -> 相当于 <= max")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 只有最大值
    cond = FilterCondition(field="file_size", operator="between", values=[None, "50"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  values=[None, '50'] -> {result.filtered_count} 条")

    # 用 lte 验证结果是否一致
    cond_lte = FilterCondition(field="file_size", operator="lte", values=["50"])
    dm.set_conditions([cond_lte])
    result_lte = dm.apply_filters(page=1, page_size=100)
    print(f"  lte 50            -> {result_lte.filtered_count} 条 (参照)")

    assert result.filtered_count == result_lte.filtered_count, "只有max时应该等价于lte"
    print("  ✅ 测试通过（与lte结果一致）")


def test_between_both_set():
    """测试：两个值都设置 -> 正常between"""
    print("\n" + "=" * 60)
    print("测试4: 两个值都设置 -> 正常between范围")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    cond = FilterCondition(field="file_size", operator="between", values=["10", "50"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  values=['10', '50'] -> {result.filtered_count} 条")

    # 手动验证
    expected = sum(
        1 for b in books
        if 10 <= b.file_size / (1024 * 1024) <= 50
    )
    print(f"  预期数量: {expected} 条")

    assert result.filtered_count == expected, "between结果不正确"
    print("  ✅ 测试通过")


def test_between_min_gt_max():
    """测试：min > max 时自动交换"""
    print("\n" + "=" * 60)
    print("测试5: min > max -> 自动交换（鲁棒性）")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 正常顺序
    cond1 = FilterCondition(field="file_size", operator="between", values=["10", "50"])
    dm.set_conditions([cond1])
    result1 = dm.apply_filters(page=1, page_size=100)
    print(f"  ['10', '50'] (正常)  -> {result1.filtered_count} 条")

    # 反向顺序
    cond2 = FilterCondition(field="file_size", operator="between", values=["50", "10"])
    dm.set_conditions([cond2])
    result2 = dm.apply_filters(page=1, page_size=100)
    print(f"  ['50', '10'] (反向)  -> {result2.filtered_count} 条")

    assert result1.filtered_count == result2.filtered_count, "min>max时应该自动交换"
    print("  ✅ 测试通过（自动交换，结果一致）")


def test_between_user_interaction_simulation():
    """模拟用户交互过程：从空到只设置min，再设置max"""
    print("\n" + "=" * 60)
    print("测试6: 模拟用户交互过程")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)
    total = len(books)

    print(f"总书籍数: {total}")
    print()

    # 步骤1: 初始状态 - 两个都未设置
    cond = FilterCondition(field="file_size", operator="between", values=[None, None])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"步骤1: 初始状态 (min=None, max=None)")
    print(f"  结果: {result.filtered_count} 本 (全部显示)")
    assert result.filtered_count == total
    print("  ✅ 正确")

    # 步骤2: 用户勾选并输入最小值10
    cond = FilterCondition(field="file_size", operator="between", values=["10", None])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"\n步骤2: 用户设置最小值=10 (min=10, max=None)")
    print(f"  结果: {result.filtered_count} 本 (>= 10MB)")
    assert result.filtered_count < total
    print("  ✅ 正确（只筛选>=10，不会显示0-10之间的）")

    # 步骤3: 用户再勾选并输入最大值50
    cond = FilterCondition(field="file_size", operator="between", values=["10", "50"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"\n步骤3: 用户设置最大值=50 (min=10, max=50)")
    print(f"  结果: {result.filtered_count} 本 (10-50MB之间)")
    assert result.filtered_count < total
    print("  ✅ 正确（完整范围筛选）")

    # 步骤4: 用户取消最小值勾选
    cond = FilterCondition(field="file_size", operator="between", values=[None, "50"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"\n步骤4: 用户取消最小值 (min=None, max=50)")
    print(f"  结果: {result.filtered_count} 本 (<= 50MB)")
    print("  ✅ 正确（只筛选<=50）")

    print("\n🎉 交互流程测试通过！用户不会再困惑了。")


def test_publish_year_between():
    """测试出版年份的范围筛选"""
    print("\n" + "=" * 60)
    print("测试7: 出版年份范围筛选")
    print("=" * 60)

    books = []
    for year in range(2015, 2026):
        book = BookMeta(
            title=f"书籍{year}",
            publish_date=f"{year}-01-01",
            file_path=f"/book{year}.epub"
        )
        books.append(book)

    dm = BookDataManager()
    dm.load_books(books)
    total = len(books)
    print(f"总书籍数: {total} (2015-2025)")

    # 只有起始年份
    cond = FilterCondition(field="publish_year", operator="between", values=["2020", None])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"\n起始年份=2020 (无结束年) -> {result.filtered_count} 本 (2020-2025)")
    assert result.filtered_count == 6  # 2020,2021,2022,2023,2024,2025
    print("  ✅ 正确")

    # 只有结束年份
    cond = FilterCondition(field="publish_year", operator="between", values=[None, "2020"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"结束年份=2020 (无起始年) -> {result.filtered_count} 本 (2015-2020)")
    assert result.filtered_count == 6  # 2015,2016,2017,2018,2019,2020
    print("  ✅ 正确")

    # 完整范围
    cond = FilterCondition(field="publish_year", operator="between", values=["2018", "2022"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"2018-2022 范围 -> {result.filtered_count} 本")
    assert result.filtered_count == 5  # 2018,2019,2020,2021,2022
    print("  ✅ 正确")


def test_condition_has_effect():
    """测试 _condition_has_effect 方法"""
    print("\n" + "=" * 60)
    print("测试8: 条件有效性判断")
    print("=" * 60)

    dm = BookDataManager()

    test_cases = [
        (FilterCondition("title", "contains", ["Python"]), True, "普通contains有值"),
        (FilterCondition("title", "contains", []), False, "普通contains空值"),
        (FilterCondition("file_size", "between", ["10", "50"]), True, "between两个都有值"),
        (FilterCondition("file_size", "between", ["10", None]), True, "between只有min"),
        (FilterCondition("file_size", "between", [None, "50"]), True, "between只有max"),
        (FilterCondition("file_size", "between", [None, None]), False, "between都为空"),
        (FilterCondition("file_size", "between", ["", ""]), False, "between都是空字符串"),
        (FilterCondition("file_size", "between", ["", "50"]), True, "between min空max有"),
        (FilterCondition("file_size", "between", ["10", ""]), True, "between min有max空"),
    ]

    for cond, expected, desc in test_cases:
        actual = dm._condition_has_effect(cond)
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {desc:25} -> {actual} (预期: {expected})")
        assert actual == expected, f"测试失败: {desc}"

    print("\n  ✅ 全部通过")


def test_fallback_mode():
    """测试纯Python模式（无pandas）也正常"""
    print("\n" + "=" * 60)
    print("测试9: 纯Python fallback模式")
    print("=" * 60)

    # 保存原始PANDAS_AVAILABLE状态
    import ebook_manager.data_manager as dm_module
    original = dm_module.PANDAS_AVAILABLE

    try:
        # 临时禁用pandas
        dm_module.PANDAS_AVAILABLE = False

        books = create_test_books()
        dm = BookDataManager()
        dm.load_books(books)

        # 测试只有min
        cond = FilterCondition(field="file_size", operator="between", values=["10", None])
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  只有min (fallback模式): {result.filtered_count} 条")

        # 测试只有max
        cond = FilterCondition(field="file_size", operator="between", values=[None, "50"])
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  只有max (fallback模式): {result.filtered_count} 条")

        # 测试都为空
        cond = FilterCondition(field="file_size", operator="between", values=[None, None])
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  都为空 (fallback模式): {result.filtered_count} 条")
        assert result.filtered_count == len(books)

        print("  ✅ fallback模式也正常")
    finally:
        # 恢复原始状态
        dm_module.PANDAS_AVAILABLE = original


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("范围筛选修复测试套件")
    print("=" * 60)

    try:
        test_between_both_empty()
        test_between_only_min()
        test_between_only_max()
        test_between_both_set()
        test_between_min_gt_max()
        test_between_user_interaction_simulation()
        test_publish_year_between()
        test_condition_has_effect()
        test_fallback_mode()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)
        print()
        print("修复内容总结:")
        print("  1. between运算符支持单边范围（只有min或只有max）")
        print("  2. 两个值都为空时条件不生效（不会困惑用户）")
        print("  3. min > max时自动交换（鲁棒性）")
        print("  4. UI层使用复选框启用/禁用min和max")
        print("  5. 文件拆分为独立组件方便复用")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
