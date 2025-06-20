from flask import jsonify

# 统一成功响应
def success_response(data=None, msg='请求成功', code=200):
    return jsonify({
        'code': code,
        'msg': msg,
        'data': data
    }), code

# 统一错误响应
def error_response(msg='请求失败', code=400, data=None):
    return jsonify({
        'code': code,
        'msg': msg,
        'data': data
    }), code

# 401 未授权
def unauthorized_response(msg='未授权'):
    return error_response(msg=msg, code=401)

# 403 禁止访问
def forbidden_response(msg='没有权限'):
    return error_response(msg=msg, code=403)

# 404 找不到资源
def not_found_response(msg='资源不存在'):
    return error_response(msg=msg, code=404)

# 422 参数错误
def bad_request(msg='参数不合法'):
    return error_response(msg=msg, code=422)
