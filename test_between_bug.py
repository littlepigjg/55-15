"""测试范围筛选的bug"""
from ebook_manager.models import BookMeta
from ebook_manager.data_manager import BookDataManager, FilterCondition


def create_test_books():
    books = []
    for i in range(20):
        size_mb = 5 + i * 3  # 5, 8, 11, 14, ... 62
        book = BookMeta(
            title=f"书籍{i}",
            author="作者",
            file_format="epub",
            file_size=int(size_mb * 1024 * 1024),
            file_path=f"/book{i}.epub"
        )
        books.append(book)
        print(f"书籍{i}: {size_mb:.1f} MB")
    return books


def test_between_operator():
    print("=" * 60)
    print("测试 between 运算符")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    print(f"\n总书籍数: {len(books)}")

    # 测试1: 用 gte 筛选 >= 10
    print("\n" + "-" * 40)
    print("测试1: file_size >= 10 (gte)")
    cond = FilterCondition(field="file_size", operator="gte", values=["10"])
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"匹配数量: {result.filtered_count}")
    for b in result.books:
        size_mb = b.file_size / (1024 * 1024)
        print(f"  {b.title}: {size_mb:.1f} MB")

    # 测试2: 用 between 筛选 10-50
    print("\n" + "-" * 40)
    print("测试2: file_size between 10 and 50")
    cond = FilterCondition(field="file_size", operator="between", values=["10", "50"])
    print(f"条件: {cond.field} {cond.operator} {cond.values}")
    dm.set_conditions([cond])
    result = dm.apply_filters(page=1, page_size=100)
    print(f"匹配数量: {result.filtered_count}")
    for b in result.books:
        size_mb = b.file_size / (1024 * 1024)
        print(f"  {b.title}: {size_mb:.1f} MB")

    # 测试3: 调试 - 直接看dataframe中的值
    print("\n" + "-" * 40)
    print("调试: 查看DataFrame中的file_size值")
    if dm._df is not None:
        print("DataFrame file_size列:")
        print(dm._df['file_size'].head(10).to_string())
        print(f"\n数据类型: {dm._df['file_size'].dtype}")

        # 手动测试between
        min_val = 10.0
        max_val = 50.0
        num_series = dm._df['file_size']
        mask = (num_series >= min_val) & (num_series <= max_val)
        print(f"\n手动计算between结果: {mask.sum()} 条匹配")
        print(f"匹配的索引: {list(mask[mask].index)}")

    # 测试4: 检查values格式
    print("\n" + "-" * 40)
    print("测试4: 不同values格式")
    test_values = [
        ["10", "50"],           # 字符串
        [10, 50],               # 整数
        ["10.0", "50.0"],       # 浮点数字符串
        [10.0, 50.0],           # 浮点数
        ["10.5", "50.5"],       # 带小数的字符串
    ]

    for vals in test_values:
        cond = FilterCondition(field="file_size", operator="between", values=vals)
        dm.set_conditions([cond])
        result = dm.apply_filters(page=1, page_size=100)
        print(f"  values={vals} -> {result.filtered_count} 条")


if __name__ == "__main__":
    test_between_operator()
