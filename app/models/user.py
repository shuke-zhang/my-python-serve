from app.models import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # ✅ 数据库主键
    user_id = db.Column(db.Integer, unique=True, nullable=False)     # ✅ 你手动生成的业务 ID

    name = db.Column(db.String(50), nullable=False)
    nick_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    id_card = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(10))
    avatar = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    remark = db.Column(db.String(255))
    status = db.Column(db.String(10))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "nick_name": self.nick_name,
            "email": self.email,
            "phone": self.phone,
            "id_card": self.id_card,
            "sex": self.sex,
            "avatar": self.avatar,
            "password": self.password,
            "remark": self.remark,
            "status": self.status,
        }
