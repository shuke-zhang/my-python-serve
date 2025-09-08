from datetime import datetime
from sqlalchemy import UniqueConstraint
from app.models import db

class UploadStatusEnum(str):
    initiated = "initiated"
    receiving = "receiving"
    committed = "committed"
    aborted = "aborted"

class FileStatusEnum(str):
    active = "active"
    deleted = "deleted"

class FileEntry(db.Model):
    __tablename__ = "uploaded_file"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_name = db.Column(db.String(512), nullable=False, index=True)
    public_name = db.Column(db.String(512), nullable=False, unique=True, index=True)
    content_type = db.Column(db.String(255), nullable=True)
    size = db.Column(db.BigInteger, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False, index=True)
    storage_path = db.Column(db.Text, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(16), default=FileStatusEnum.active, nullable=False)
    note = db.Column(db.Text, nullable=True)

class ResumableUpload(db.Model):
    __tablename__ = "uploads"
    id = db.Column(db.String(36), primary_key=True)  # uuid4
    filename = db.Column(db.String(512), nullable=False)
    expected_size = db.Column(db.BigInteger, nullable=True)
    expected_sha256 = db.Column(db.String(64), nullable=True)
    temp_path = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), default=UploadStatusEnum.initiated, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    chunks = db.relationship("UploadChunk", back_populates="upload", cascade="all, delete-orphan")

class UploadChunk(db.Model):
    __tablename__ = "upload_chunks"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    upload_id = db.Column(db.String(36), db.ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    index = db.Column(db.Integer, nullable=False)  # 0-based
    size = db.Column(db.BigInteger, nullable=False)
    sha256 = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    upload = db.relationship("ResumableUpload", back_populates="chunks")
    __table_args__ = (UniqueConstraint("upload_id", "index", name="uq_upload_chunk"),)

    # 可选：__repr__ 便于调试
