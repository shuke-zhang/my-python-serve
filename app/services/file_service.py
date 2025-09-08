import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from flask import url_for
from werkzeug.datastructures import FileStorage
from flask import current_app

from app.models import db
from app.models.file import (
    FileEntry, ResumableUpload, UploadChunk,
    UploadStatusEnum, FileStatusEnum,
)
from app.vendors.settings import Settings
from app.vendors.storage import (
    sanitize_filename, split_name, atomic_move, ensure_parent, sha256_of_path,
)
import hashlib

class FileService:
    """
    文件上传/分片/查询 的业务逻辑
    """

    # ---------- small helpers ----------
    def _ensure_unique_public_name(self, base_name: str, sha256_val: str) -> str:
        candidate = base_name
        stem, suffix = split_name(base_name)
        i = 1
        while True:
            existing = FileEntry.query.filter_by(public_name=candidate).first()
            if not existing:
                return candidate
            if existing.sha256 == sha256_val:
                return existing.public_name
            candidate = f"{stem}-{i}{suffix}"
            i += 1

    def _file_to_dict(self, entry, request_base_url: str | None = None):
         public_url = url_for("file.public_by_name", public_name=entry.public_name, _external=True)
         download_url = url_for("file.download_file", file_id=entry.id, _external=True)
         return {
        "id": entry.id,
        "original_name": entry.original_name,
        "public_name": entry.public_name,
        "public_url": public_url,        # 例如 http://192.168.3.117:5000/api/p/123.png
        "download_url": download_url,    # 例如 http://192.168.3.117:5000/api/download/17
        # ... 其他字段
    }

    # ---------- 单次上传 ----------
    def single_shot_upload(self, file: FileStorage, note: Optional[str]) -> FileEntry:
        tmp_path = Settings.TMP_DIR / f"{uuid.uuid4()}.part"
        ensure_parent(tmp_path)

        size = 0
        h = hashlib.sha256()
        with tmp_path.open("wb") as out:
            while True:
                data = file.stream.read(Settings.CHUNK_SIZE)
                if not data:
                    break
                out.write(data)
                size += len(data)
                h.update(data)
        checksum = h.hexdigest()

        existing = FileEntry.query.filter_by(sha256=checksum, status=FileStatusEnum.active).first()
        if existing:
            tmp_path.unlink(missing_ok=True)
            return existing

        final_path = Settings.STORAGE_DIR / file.filename
        atomic_move(tmp_path, final_path)

        safe_name = sanitize_filename(file.filename)
        public_name = self._ensure_unique_public_name(safe_name, checksum)

        entry = FileEntry(
            original_name=file.filename,
            public_name=public_name,
            content_type=file.mimetype,
            size=size,
            sha256=checksum,
            storage_path=str(final_path),
            note=note,
            created_at=datetime.utcnow(),
            status=FileStatusEnum.active,
        )
        db.session.add(entry)
        db.session.commit()
        db.session.refresh(entry)
        return entry

    # ---------- 分片生命周期 ----------
    def initiate_upload(self, filename: str, expected_size: Optional[int], expected_sha256: Optional[str]) -> str:
        upload_id = str(uuid.uuid4())
        temp_path = Settings.TMP_DIR / f"{upload_id}.part"
        ensure_parent(temp_path)
        temp_path.touch(exist_ok=False)

        up = ResumableUpload(
            id=upload_id,
            filename=filename,
            expected_size=expected_size,
            expected_sha256=(expected_sha256.lower() if expected_sha256 else None),
            temp_path=str(temp_path),
            status=UploadStatusEnum.initiated,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(up)
        db.session.commit()
        return upload_id

    def put_chunk(self, upload_id: str, index: int, chunk: FileStorage, chunk_sha256: Optional[str]) -> dict:
        up = ResumableUpload.query.get(upload_id)
        if not up or up.status in (UploadStatusEnum.committed, UploadStatusEnum.aborted):
            raise ValueError("Upload not found or already finalized")

        temp_path = Path(up.temp_path)
        expected_index = UploadChunk.query.filter_by(upload_id=upload_id).count()
        if index != expected_index:
            raise ValueError(f"Unexpected chunk index {index}, expected {expected_index}")

        h = hashlib.sha256()
        bytes_written = 0
        with temp_path.open("ab") as out:
            while True:
                data = chunk.stream.read(Settings.CHUNK_SIZE)
                if not data:
                    break
                out.write(data)
                bytes_written += len(data)
                h.update(data)
        chk = h.hexdigest()

        if chunk_sha256 and chunk_sha256.lower() != chk:
            # 回滚尾部
            with temp_path.open("rb+") as f:
                f.truncate(temp_path.stat().st_size - bytes_written)
            raise ValueError("Chunk checksum mismatch")

        up.status = UploadStatusEnum.receiving
        up.updated_at = datetime.utcnow()
        db.session.add(UploadChunk(upload_id=upload_id, index=index, size=bytes_written, sha256=chk))
        db.session.commit()

        received = temp_path.stat().st_size
        return {
            "upload_id": upload_id,
            "status": up.status,
            "received_bytes": received,
            "next_index": index + 1,
        }

    def commit_upload(self, upload_id: str, expected_size: Optional[int], expected_sha256: Optional[str], content_type: Optional[str], note: Optional[str]) -> FileEntry:
        up = ResumableUpload.query.get(upload_id)
        if not up or up.status in (UploadStatusEnum.committed, UploadStatusEnum.aborted):
            raise ValueError("Upload not found or already finalized")

        temp_path = Path(up.temp_path)
        if not temp_path.exists():
            raise FileNotFoundError("Temporary file missing")

        size = temp_path.stat().st_size
        exp_size = expected_size or up.expected_size
        if exp_size is not None and size != exp_size:
            raise ValueError(f"Size mismatch: got {size}, expected {exp_size}")

        checksum = sha256_of_path(temp_path)
        exp_hash = (expected_sha256 or up.expected_sha256)
        if exp_hash and checksum.lower() != exp_hash.lower():
            raise ValueError("SHA256 mismatch")

        existing = FileEntry.query.filter_by(sha256=checksum, status=FileStatusEnum.active).first()
        if existing:
            temp_path.unlink(missing_ok=True)
            up.status = UploadStatusEnum.committed
            up.updated_at = datetime.utcnow()
            db.session.commit()
            return existing

        final_path = Settings.STORAGE_DIR / up.filename
        atomic_move(temp_path, final_path)

        safe_name = sanitize_filename(up.filename)
        public_name = self._ensure_unique_public_name(safe_name, checksum)

        entry = FileEntry(
            original_name=up.filename,
            public_name=public_name,
            content_type=content_type,
            size=size,
            sha256=checksum,
            storage_path=str(final_path),
            created_at=datetime.utcnow(),
            status=FileStatusEnum.active,
            note=note,
        )
        db.session.add(entry)
        up.status = UploadStatusEnum.committed
        up.updated_at = datetime.utcnow()
        db.session.commit()
        db.session.refresh(entry)
        return entry

    def abort_upload(self, upload_id: str) -> None:
        up = ResumableUpload.query.get(upload_id)
        if not up:
            raise ValueError("会话不存在")
        Path(up.temp_path).unlink(missing_ok=True)
        UploadChunk.query.filter_by(upload_id=upload_id).delete()
        up.status = UploadStatusEnum.aborted
        up.updated_at = datetime.utcnow()
        db.session.commit()

    # ---------- 查询 / 下载 ----------
    def list_files(self) -> list[FileEntry]:
        return FileEntry.query.filter_by(status=FileStatusEnum.active).order_by(FileEntry.created_at.desc()).all()

    def get_file(self, file_id: int) -> Optional[FileEntry]:
        row = FileEntry.query.get(file_id)
        if not row or row.status != FileStatusEnum.active:
            return None
        return row
