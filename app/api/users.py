from flask import Blueprint, request
from app.models.user import User
from app.models import db
from utils.response import success_response, error_response
from utils.pagination import paginate

user_bp = Blueprint('user', __name__, url_prefix='/api')

# 创建用户
@user_bp.route('/user/register', methods=['POST'])
def register():
    data = request.get_json(force=True)

    name = data.get("name")
    password = data.get("password")
    nick_name = data.get("nick_name")
    email = data.get("email")
    phone = data.get("phone")
    id_card = data.get("id_card")
    sex = data.get("sex")
    avatar = data.get("avatar")
    remark = data.get("remark")
    status = data.get("status")

    if not name or not password:
        return error_response("用户名和密码为必填项")

    try:
        # ⭐ 1. 查询当前最大 user_id，并加 1
        max_user = db.session.query(User.user_id).order_by(User.user_id.desc()).first()
        next_user_id = (max_user[0] + 1) if max_user else 1

        # ⭐ 2. 创建新用户，使用手动生成的 user_id
        new_user = User(
            user_id=next_user_id,
            name=name,
            password=password,
            nick_name=nick_name,
            email=email,
            phone=phone,
            id_card=id_card,
            sex=sex,
            avatar=avatar,
            remark=remark,
            status=status,
        )

        db.session.add(new_user)
        db.session.commit()
        return success_response(
            msg="用户创建成功",
            data={"user_id": new_user.user_id, "name": new_user.name}
        )
    except Exception as e:
        db.session.rollback()
        return error_response(f"创建失败: {str(e)}")

# 查询所有用户
@user_bp.route('/user/list', methods=['GET'])
def get_users():
    query = db.session.query(User)
    users, total = paginate(query)
    items, total = paginate(query)
    print(f"分页信息: pageNum={request.args.get('pageNum')}, pageSize={request.args.get('pageSize')}, total={total}, 当前页数据量={len(items)}")
    return success_response({
        "list": [user.to_dict() for user in users],
        "total": total
    })
# 查询单个用户
@user_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response('用户不存在')
    return success_response(user.to_dict())

# 更新用户
@user_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response('用户不存在')
    data = request.json
    for field in ['name', 'nick_name', 'email', 'phone', 'id_card', 'sex', 'avatar', 'password', 'remark', 'status']:
        if field in data:
            setattr(user, field, data[field])
    try:
        db.session.commit()
        return success_response('用户更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')

# 删除用户
@user_bp.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response('用户不存在')
    try:
        db.session.delete(user)
        db.session.commit()
        return success_response('用户删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除失败: {str(e)}')
