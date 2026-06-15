"""测试值格式问题"""
from ebook_manager.models import BookMeta
from ebook_manager.data_manager import BookDataManager, FilterCondition


def test_value_formats():
    print("=" * 60)
    print("测试不同值格式")
    print("=" * 60)

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

    # 测试不同格式的between值
    test_cases = [
        ["10", "50"],           # 整数字符串
        ["10.0", "50.0"],       # 浮点数字符串
        [10, 50],               # 整数
        [10.0, 50.0],           # 浮点数
        ["10.5", "50.5"],       # 带小数
        [" 10 ", " 50 "],       # 带空格
    ]

    for vals in test_cases:
        cond = FilterCondition(field="file_size", operator="between", values=vals)
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  {vals!r:20} -> {result.filtered_count:3d} 条")

    # 测试单值比较
    print("\n" + "=" * 60)
    print("测试单值比较（gte）")
    print("=" * 60)

    test_values = ["10", "10.0", 10, 10.0, " 10 "]
    for val in test_values:
        cond = FilterCondition(field="file_size", operator="gte", values=[val])
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  gte {val!r:15} -> {result.filtered_count:3d} 条")

    # 测试边界值
    print("\n" + "=" * 60)
    print("测试边界值 (正好11.0MB的书)")
    print("=" * 60)

    # 书籍2是11.0MB
    boundary_tests = [
        (["11", "11"], "等于11"),
        (["10.99", "11.01"], "包含11"),
        (["11.0", "11.0"], "等于11.0"),
    ]

    for vals, desc in boundary_tests:
        cond = FilterCondition(field="file_size", operator="between", values=vals)
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  {vals!r:20} {desc:15} -> {result.filtered_count:3d} 条")
        for b in result.books:
            size_mb = b.file_size / (1024 * 1024)
            print(f"    -> {b.title}: {size_mb:.2f} MB")

    # 测试：检查DataFrame中的file_size实际值
    print("\n" + "=" * 60)
    print("检查DataFrame中的实际值")
    print("=" * 60)

    if hasattr(dm._df, 'iloc'):
        for i in range(5):
            val = dm._df.iloc[i]['file_size']
            print(f"  行{i}: file_size = {val}, type = {type(val)}")


if __name__ == "__main__":
    test_value_formats()
