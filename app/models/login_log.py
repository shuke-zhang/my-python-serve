from app.models import db
import datetime

class LoginLog(db.Model):
    __tablename__ = 'login_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    ip = db.Column(db.String(64))
    time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
