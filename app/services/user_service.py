from app.models.user import User
from app.models import db
from werkzeug.security import generate_password_hash

def create_user(data):
    max_user = db.session.query(User.user_id).order_by(User.user_id.desc()).first()
    next_user_id = (max_user[0] + 1) if max_user else 1

    new_user = User(
        user_id=next_user_id,
        name=data["name"],
        password= generate_password_hash(data['password'])  ,
        nick_name=data.get("nick_name"),
        email=data.get("email"),
        phone=data.get("phone"),
        id_card=data.get("id_card"),
        sex=data.get("sex"),
        avatar=data.get("avatar"),
        remark=data.get("remark"),
        status=data.get("status"),
    )

    db.session.add(new_user)
    db.session.commit()
    return new_user
# ✅ 更新用户信息
def update_user_info(user_id, update_data):
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return None, "用户不存在"

    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    try:
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, f"更新失败: {str(e)}"
    
# ✅ 删除用户函数
def delete_user_by_id(user_id: int) -> tuple[bool, str]:
    """
    根据 user_id 删除用户。

    :param user_id: 用户ID
    :return: (是否成功, 提示信息)
    """
    try:
        user = User.query.filter_by(user_id=user_id).first()
        print('删除时查询到的用户:', user)

        if not user:
            return False, "用户不存在"

        db.session.delete(user)
        db.session.commit()
        return True, "用户删除成功"

    except Exception as e:
        db.session.rollback()
        return False, f"删除失败: {str(e)}"
