from app.models.user import User
from app.models import db

def create_user_service(data):
    new_user = User(**data)
    db.session.add(new_user)
    db.session.commit()

def update_user_service(user_id, data):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("用户不存在")

    for key, value in data.items():
        setattr(user, key, value)
    
    db.session.commit()
