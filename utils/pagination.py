from flask import request
from utils.response import error_response  # 假设你项目中有统一响应工具

def paginate(query, default_page_num=1, default_page_size=10, max_page_size=100):
    from flask import request

    page_num_raw = request.args.get('pageNum')
    page_size_raw = request.args.get('pageSize')

    if page_num_raw is None or page_size_raw is None:
        return error_response("分页参数缺失：必须同时提供 pageNum 和 pageSize")

    try:
        page_num = int(page_num_raw)
        page_size = int(page_size_raw)
    except ValueError:
        return error_response("分页参数类型错误：必须是整数")

    if page_num < 1 or page_size < 1:
        return error_response("分页参数必须为正整数")

    if page_size > max_page_size:
        return error_response(f"单页最多支持 {max_page_size} 条数据")

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    if total > 0 and page_num > total_pages:
        return error_response(f"pageNum 超出最大页数（{total_pages}），请检查参数顺序是否错误")

    items = query.offset((page_num - 1) * page_size).limit(page_size).all()
    return items, total