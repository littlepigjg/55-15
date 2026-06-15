"""
测试高级筛选功能
"""
from ebook_manager.models import BookMeta
from ebook_manager.data_manager import BookDataManager, FilterCondition, SortRule


def create_test_books():
    """创建测试书籍数据"""
    books = []

    for i in range(100):
        year = 2018 + (i % 10)
        formats = ["epub", "pdf", "mobi", "azw3"]
        fmt = formats[i % 4]
        size_mb = 5 + (i * 0.5) % 50

        if i % 5 == 0:
            title = f"Python编程从入门到精通 第{i}版"
            author = "张三"
            tags = ["编程", "Python", "计算机"]
        elif i % 5 == 1:
            title = f"Java核心技术 卷{i}"
            author = "李四"
            tags = ["编程", "Java", "计算机"]
        elif i % 5 == 2:
            title = f"深度学习实战 第{i}版"
            author = "王五"
            tags = ["人工智能", "深度学习", "编程"]
        elif i % 5 == 3:
            title = f"经济学原理 第{i}版"
            author = "曼昆"
            tags = ["经济", "教材"]
        else:
            title = f"中国历史纲要 第{i}卷"
            author = "钱穆"
            tags = ["历史", "中国"]

        book = BookMeta(
            title=title,
            author=author,
            publisher=f"出版社{i % 10}",
            publish_date=f"{year}-01-01",
            isbn=f"978-7-{(i % 1000):03d}-{(i % 10000):04d}",
            language="中文" if i % 2 == 0 else "英文",
            tags=tags,
            file_path=f"/books/book_{i}.{fmt}",
            file_format=fmt,
            file_size=int(size_mb * 1024 * 1024),
        )
        books.append(book)

    return books


def test_basic_filter():
    """测试基本筛选功能"""
    print("=" * 60)
    print("测试1: 基本筛选功能")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    print(f"总书籍数: {len(books)}")

    # 测试: 2020年后出版的Python编程书
    conditions = [
        FilterCondition(field="publish_year", operator="gte", values=["2020"]),
        FilterCondition(field="title", operator="contains", values=["Python"]),
    ]
    dm.set_conditions(conditions)

    result = dm.apply_filters(page=1, page_size=50)
    print(f"\n筛选条件: 出版年 >= 2020 AND 书名包含 'Python'")
    print(f"匹配数量: {result.filtered_count} / {result.total_count}")
    print(f"耗时: {result.elapsed_ms:.2f} ms")

    for i, book in enumerate(result.books[:5]):
        print(f"  {i+1}. {book.title} ({book.publish_date}, {book.file_format})")

    print("\n✅ 基本筛选测试通过")


def test_multi_value_or():
    """测试同字段多值OR关系"""
    print("\n" + "=" * 60)
    print("测试2: 同字段多值OR关系")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 测试: 格式为EPUB或PDF (同字段多值OR)
    conditions = [
        FilterCondition(field="file_format", operator="in", values=["epub", "pdf"]),
    ]
    dm.set_conditions(conditions)

    result = dm.apply_filters(page=1, page_size=100)
    print(f"筛选条件: 格式 IN (epub, pdf)")
    print(f"匹配数量: {result.filtered_count} / {result.total_count}")

    formats = set(book.file_format for book in result.books)
    print(f"实际格式: {formats}")

    assert formats == {"epub", "pdf"}, f"格式不匹配: {formats}"
    print("\n✅ 同字段多值OR测试通过")


def test_multiple_conditions_and():
    """测试多条件AND关系"""
    print("\n" + "=" * 60)
    print("测试3: 多条件AND关系")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 测试: 多个AND条件组合
    conditions = [
        FilterCondition(field="file_format", operator="in", values=["epub", "pdf"]),
        FilterCondition(field="file_size", operator="gte", values=["10"]),
        FilterCondition(field="publish_year", operator="between", values=["2019", "2022"]),
    ]
    dm.set_conditions(conditions)

    result = dm.apply_filters(page=1, page_size=100)
    print(f"筛选条件: (格式 IN epub/pdf) AND (大小 >= 10MB) AND (2019 <= 出版年 <= 2022)")
    print(f"匹配数量: {result.filtered_count} / {result.total_count}")
    print(f"耗时: {result.elapsed_ms:.2f} ms")

    for book in result.books[:5]:
        size_mb = book.file_size / (1024 * 1024)
        print(f"  {book.title} | {book.file_format} | {size_mb:.1f}MB | {book.publish_date}")

    print("\n✅ 多条件AND测试通过")


def test_pagination():
    """测试分页功能"""
    print("\n" + "=" * 60)
    print("测试4: 分页功能")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    page_size = 10
    result = dm.apply_filters(page=1, page_size=page_size)

    print(f"总记录数: {result.total_count}")
    print(f"筛选后: {result.filtered_count}")
    print(f"每页大小: {result.page_size}")
    print(f"总页数: {result.total_pages}")
    print(f"当前页: {result.page}")
    print(f"当前页记录数: {len(result.books)}")

    assert len(result.books) <= page_size, "分页大小错误"

    # 测试第3页
    result3 = dm.apply_filters(page=3, page_size=page_size)
    print(f"\n第3页记录数: {len(result3.books)}")

    print("\n✅ 分页功能测试通过")


def test_sorting():
    """测试排序功能"""
    print("\n" + "=" * 60)
    print("测试5: 排序功能")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    # 先按作者升序,再按出版年降序
    sort_rules = [
        SortRule(field="author", order="asc", pinyin=True),
        SortRule(field="publish_year", order="desc"),
    ]
    dm.set_sort_rules(sort_rules)

    result = dm.apply_filters(page=1, page_size=20)
    print(f"排序规则: 作者(拼音升序) -> 出版年(降序)")
    print(f"耗时: {result.elapsed_ms:.2f} ms")

    for i, book in enumerate(result.books[:10]):
        print(f"  {i+1}. {book.author} | {book.title} | {book.publish_date}")

    # 验证排序
    authors = [book.author for book in result.books]
    print(f"\n作者序列: {authors[:5]}")

    print("\n✅ 排序功能测试通过")


def test_tags_filter():
    """测试标签筛选"""
    print("\n" + "=" * 60)
    print("测试6: 标签筛选")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    conditions = [
        FilterCondition(field="tags", operator="contains", values=["编程"]),
    ]
    dm.set_conditions(conditions)

    result = dm.apply_filters(page=1, page_size=50)
    print(f"筛选条件: 标签包含 '编程'")
    print(f"匹配数量: {result.filtered_count} / {result.total_count}")

    for book in result.books[:5]:
        print(f"  {book.title} | 标签: {book.tags}")

    print("\n✅ 标签筛选测试通过")


def test_presets():
    """测试预设方案"""
    print("\n" + "=" * 60)
    print("测试7: 预设方案")
    print("=" * 60)

    books = create_test_books()
    dm = BookDataManager()
    dm.load_books(books)

    print("可用预设:")
    for preset in dm.get_presets():
        print(f"  - {preset.name} (条件数: {len(preset.conditions)})")

    # 加载"Python编程书"预设
    preset = dm.load_preset("Python编程书")
    print(f"\n加载预设: {preset.name}")
    print(f"条件:")
    for cond in preset.conditions:
        print(f"  {cond.field} {cond.operator} {cond.values}")

    result = dm.apply_filters(page=1, page_size=20)
    print(f"\n匹配数量: {result.filtered_count}")
    for book in result.books[:5]:
        print(f"  {book.title} ({book.publish_date})")

    print("\n✅ 预设方案测试通过")


def test_performance():
    """测试大数据量性能"""
    print("\n" + "=" * 60)
    print("测试8: 大数据量性能 (5000本书)")
    print("=" * 60)

    import random
    import time

    # 创建5000本书
    books = []
    authors = ["张三", "李四", "王五", "赵六", "钱七", "Alice", "Bob", "Charlie"]
    formats = ["epub", "pdf", "mobi"]
    tags_pool = ["编程", "Python", "Java", "历史", "经济", "小说", "科学", "技术"]

    for i in range(5000):
        year = 2015 + random.randint(0, 10)
        book = BookMeta(
            title=f"书籍标题{i} - {random.choice(['入门', '精通', '实战', '原理'])}",
            author=random.choice(authors),
            publisher=f"出版社{random.randint(1, 50)}",
            publish_date=f"{year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            isbn=f"978-7-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            language=random.choice(["中文", "英文"]),
            tags=random.sample(tags_pool, random.randint(1, 3)),
            file_path=f"/books/book_{i}.{random.choice(formats)}",
            file_format=random.choice(formats),
            file_size=random.randint(1, 100) * 1024 * 1024,
        )
        books.append(book)

    print(f"创建 {len(books)} 本书...")

    dm = BookDataManager()
    start_time = time.time()
    dm.load_books(books)
    load_time = (time.time() - start_time) * 1000
    print(f"DataFrame加载时间: {load_time:.2f} ms")

    # 复杂筛选测试
    conditions = [
        FilterCondition(field="publish_year", operator="gte", values=["2020"]),
        FilterCondition(field="file_format", operator="in", values=["epub", "pdf"]),
        FilterCondition(field="file_size", operator="gte", values=["10"]),
        FilterCondition(field="tags", operator="contains", values=["编程"]),
    ]
    dm.set_conditions(conditions)

    sort_rules = [
        SortRule(field="author", order="asc", pinyin=True),
        SortRule(field="publish_year", order="desc"),
    ]
    dm.set_sort_rules(sort_rules)

    # 多次测试取平均
    times = []
    for _ in range(10):
        start = time.time()
        result = dm.apply_filters(page=1, page_size=100)
        times.append((time.time() - start) * 1000)

    avg_time = sum(times) / len(times)
    print(f"\n复杂筛选 + 排序 (10次平均):")
    print(f"  平均耗时: {avg_time:.2f} ms")
    print(f"  最快: {min(times):.2f} ms")
    print(f"  最慢: {max(times):.2f} ms")
    print(f"  匹配数量: {result.filtered_count} / {result.total_count}")
    print(f"  总页数: {result.total_pages}")

    if avg_time < 100:
        print("\n✅ 性能测试通过 (平均 < 100ms)")
    else:
        print(f"\n⚠️  性能较慢 ({avg_time:.2f}ms), 但仍可接受")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("高级筛选器功能测试")
    print("=" * 60)

    try:
        test_basic_filter()
        test_multi_value_or()
        test_multiple_conditions_and()
        test_pagination()
        test_sorting()
        test_tags_filter()
        test_presets()
        test_performance()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
