from flask import Blueprint, request, send_file
from werkzeug.datastructures import FileStorage
from pathlib import Path
from datetime import datetime, timezone
import os

from app.services.file_service import FileService
from app.schemas.file_schema import UploadInitSchema, UploadCommitSchema, load_and_validate
from app.models.file import FileStatusEnum
from utils.response import success_response, error_response  # 复用你的工具

file_bp = Blueprint("file", __name__, url_prefix="/api")
svc = FileService()

# -------------------------
# 工具：安全生成 last_modified（优先用磁盘 mtime，回退到 created_at）
# -------------------------
def _safe_last_modified(path: Path, created_at) -> datetime | None:
    try:
        # 1) 优先使用文件真实 mtime（转为 UTC）
        mtime = path.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc)
    except Exception:
        pass

    # 2) 回退：created_at 可能是 datetime 或 str
    if isinstance(created_at, datetime):
        return created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    if isinstance(created_at, str):
        # 尝试解析 ISO 字符串；失败就返回 None（不传 last_modified）
        try:
            dt = datetime.fromisoformat(created_at)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None

# -------------------------
# 单次上传
# -------------------------
@file_bp.route("/upload", methods=["POST"])
def upload_file():
    try:
        f: FileStorage = request.files.get("file")
        note = request.form.get("note")
        if not f:
            return error_response("缺少文件字段 file")

        entry = svc.single_shot_upload(file=f, note=note)
        data = svc._file_to_dict(entry, request_base_url=request.base_url.replace(request.path, ""))
        return success_response(data=data, msg="上传成功")
    except Exception as e:
        return error_response(f"上传失败: {str(e)}")

# -------------------------
# 分片上传：创建会话
# -------------------------
@file_bp.route("/uploads/initiate", methods=["POST"])
def initiate_upload():
    try:
        payload = load_and_validate(UploadInitSchema(), request.get_json())
        upload_id = svc.initiate_upload(
            filename=payload["filename"],
            expected_size=payload.get("expected_size"),
            expected_sha256=payload.get("expected_sha256"),
        )
        return success_response(data={"upload_id": upload_id}, msg="创建分片会话成功")
    except ValueError as ve:
        return error_response(str(ve))
    except Exception as e:
        return error_response(f"创建分片会话失败: {str(e)}")

# -------------------------
# 分片上传：写入某片
# -------------------------
@file_bp.route("/uploads/<upload_id>/chunk", methods=["PUT"])
def put_chunk(upload_id: str):
    try:
        index_str = request.form.get("index")
        sha256_hex = request.form.get("sha256")
        chunk: FileStorage = request.files.get("chunk")
        if index_str is None or chunk is None:
            return error_response("缺少表单字段 index 或 chunk")

        index = int(index_str)
        status = svc.put_chunk(upload_id=upload_id, index=index, chunk=chunk, chunk_sha256=sha256_hex)
        return success_response(data=status, msg="分片上传成功")
    except Exception as e:
        return error_response(f"分片上传失败: {str(e)}")

# -------------------------
# 分片上传：提交合并
# -------------------------
@file_bp.route("/uploads/<upload_id>/commit", methods=["POST"])
def commit_upload(upload_id: str):
    try:
        payload = load_and_validate(UploadCommitSchema(), request.get_json())
        entry = svc.commit_upload(
            upload_id=upload_id,
            expected_size=payload.get("expected_size"),
            expected_sha256=payload.get("expected_sha256"),
            content_type=payload.get("content_type"),
            note=payload.get("note"),
        )
        data = svc._file_to_dict(entry, request_base_url=request.base_url.replace(request.path, ""))
        return success_response(data=data, msg="提交成功")
    except ValueError as ve:
        return error_response(str(ve))
    except FileNotFoundError as fe:
        return error_response(str(fe))
    except Exception as e:
        return error_response(f"提交失败: {str(e)}")

# -------------------------
# 分片上传：取消会话
# -------------------------
@file_bp.route("/uploads/<upload_id>/abort", methods=["POST"])
def abort_upload(upload_id: str):
    try:
        svc.abort_upload(upload_id)
        return success_response({"upload_id": upload_id}, "已取消上传")
    except Exception as e:
        return error_response(f"取消失败: {str(e)}")

# -------------------------
# 文件管理
# -------------------------
@file_bp.route("/files", methods=["GET"])
def list_files():
    rows = svc.list_files()
    base = request.base_url.replace(request.path, "")
    data = [svc._file_to_dict(r, base) for r in rows]
    return success_response(data=data, msg="查询成功")

@file_bp.route("/files/<int:file_id>", methods=["GET"])
def get_file(file_id: int):
    row = svc.get_file(file_id)
    if not row:
        return error_response("未找到文件")
    data = svc._file_to_dict(row, request.base_url.replace(request.path, ""))
    return success_response(data=data, msg="查询成功")

# -------------------------
# 下载：附件方式（浏览器触发下载）
# -------------------------
@file_bp.route("/download/<int:file_id>", methods=["GET"])
def download_file(file_id: int):
    row = svc.get_file(file_id)
    if not row:
        return error_response("文件不存在")
    path = Path(row.storage_path)
    if not path.exists():
        return error_response("磁盘缺失")

    last_modified = _safe_last_modified(path, getattr(row, "created_at", None))

    kwargs = dict(
        as_attachment=True,
        download_name=row.original_name,
        mimetype=row.content_type or "application/octet-stream",
        conditional=True,
        etag=True,
        max_age=3600,
    )
    if last_modified is not None:
        kwargs["last_modified"] = last_modified

    return send_file(str(path), **kwargs)

# -------------------------
# 直链预览：inline（不强制下载，可用于 <img src> / 浏览器预览）
#     /api/p/<public_name> 或 /api/<public_name>
# -------------------------
@file_bp.route("/p/<path:public_name>", methods=["GET"])
@file_bp.route("/<path:public_name>", methods=["GET"])
def public_by_name(public_name: str):
    from app.models.file import FileEntry, FileStatusEnum
    row = FileEntry.query.filter_by(public_name=public_name).first()
    if not row:
        return error_response("Public file not found")

    status_val = getattr(row, "status", None)
    is_active = False
    try:
        is_active = (status_val == FileStatusEnum.active)
    except Exception:
        pass
    if not is_active:
        is_active = str(status_val).lower() == "active"
    if not is_active:
        return error_response("File not active")

    path = Path(row.storage_path)
    if not path.exists():
        return error_response("File missing on disk")

    # 复用你之前的 _safe_last_modified 逻辑
    last_modified = _safe_last_modified(path, getattr(row, "created_at", None))

    kwargs = dict(
        as_attachment=False,
        mimetype=row.content_type or "application/octet-stream",
        conditional=True,
        etag=True,
        max_age=3600,
    )
    if last_modified is not None:
        kwargs["last_modified"] = last_modified

    return send_file(str(path), **kwargs)