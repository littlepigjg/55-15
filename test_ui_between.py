"""测试UI层的between问题"""
from ebook_manager.models import BookMeta
from ebook_manager.data_manager import BookDataManager, FilterCondition


def simulate_ui_between():
    """模拟UI层设置between条件的过程"""
    print("=" * 60)
    print("模拟UI层between操作")
    print("=" * 60)

    # 创建数据
    books = []
    for i in range(20):
        size_mb = 5 + i * 3
        book = BookMeta(
            title=f"书籍{i}",
            file_size=int(size_mb * 1024 * 1024),
            file_path=f"/book{i}.epub"
        )
        books.append(book)

    dm = BookDataManager()
    dm.load_books(books)
    print(f"总书籍数: {len(books)}")

    # 模拟UI操作流程
    print("\n" + "-" * 50)
    print("步骤1: 初始状态 - values=[]")
    cond = FilterCondition(field="file_size", operator="gte", values=["10"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  gte 10: {result.filtered_count} 条 (正常)")

    print("\n" + "-" * 50)
    print("步骤2: 用户切换到between运算符")
    cond.operator = "between"
    # UI会先清空values
    cond.values = []
    print(f"  清空后 values: {cond.values}")

    # 创建范围编辑器，初始值为0,0 (QSpinBox默认值)
    cond.values = ["0", "0"]
    print(f"  编辑器初始化后 values: {cond.values}")

    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  0-0: {result.filtered_count} 条 (此时还没输入)")

    print("\n" + "-" * 50)
    print("步骤3: 用户先输入最小值10")
    # 第一个输入框变化，触发_on_range_changed
    # _on_range_changed会读取两个编辑器的值
    # 此时最小值是10，最大值还是0
    cond.values = ["10", "0"]
    print(f"  values: {cond.values}")

    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  10-0: {result.filtered_count} 条 (最小值>最大值，导致0条!)")

    print("\n" + "-" * 50)
    print("步骤4: 用户再输入最大值50")
    cond.values = ["10", "50"]
    print(f"  values: {cond.values}")

    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"  10-50: {result.filtered_count} 条 (现在正常了)")

    # 关键问题：当最小值 > 最大值时，返回0条！
    print("\n" + "=" * 60)
    print("问题分析:")
    print("当用户先输入最小值(10)，再输入最大值(50)时，")
    print("中间状态是 min=10, max=0，此时 min > max")
    print("导致筛选条件变成 10 <= x <= 0，这是不可能的条件")
    print("所以显示0条记录")
    print("=" * 60)

    # 测试不同的边界情况
    print("\n" + "=" * 60)
    print("测试不同边界情况:")
    print("=" * 60)

    test_cases = [
        (["10", "50"], "正常范围"),
        (["10", "10"], "min等于max"),
        (["50", "10"], "min大于max (问题!)"),
        (["0", "0"], "都是0"),
        (["", "50"], "min为空"),
        (["10", ""], "max为空"),
    ]

    for vals, desc in test_cases:
        cond = FilterCondition(field="file_size", operator="between", values=vals)
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        status = "❌ 问题" if result.filtered_count == 0 and "问题" in desc else "✅ 正常"
        print(f"  {vals!r:15} {desc:20} -> {result.filtered_count:3d} 条 {status}")


if __name__ == "__main__":
    simulate_ui_between()
