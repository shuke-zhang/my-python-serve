from flask import Blueprint, request
from marshmallow import ValidationError
from app.models.user import User
from utils.response import success_response, error_response
from utils.pagination import paginate
from app.schemas.user_schema import UserSchema, load_and_validate
from app.services.user_service import create_user, update_user_info, delete_user_by_id

user_bp = Blueprint('user', __name__, url_prefix='/api')

# 创建用户
@user_bp.route('/user/register', methods=['POST'])
def register():
    try:
        data = load_and_validate(UserSchema(), request.get_json())
    except ValueError as e:
        return error_response(str(e))

    try:
        new_user = create_user(data)
        return success_response(data=None, msg='用户创建成功',)
    except Exception as e:
        return error_response(f"创建失败: {str(e)}")

# 查询所有用户
@user_bp.route('/user/list', methods=['GET'])
def get_users():
    query = User.query
    users, total = paginate(query)
    return success_response({
        "list": [user.to_dict() for user in users],
        "total": total
    })

# 查询单个用户
@user_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return error_response('用户不存在')
    return success_response(user.to_dict())

# 更新用户
@user_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):

    try:
        data = load_and_validate(UserSchema(), request.get_json())
    except ValueError as e:
        return error_response(str(e))

    try:
        update_user_info(user_id, data)
        return success_response('用户更新成功')
    except Exception as e:
        return error_response(f'更新失败: {str(e)}')

# 删除用户
@user_bp.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):

    try:
        delete_user_by_id(user_id)
        return success_response('用户删除成功')
    except Exception as e:
        return error_response(f'删除失败: {str(e)}')
