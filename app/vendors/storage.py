import hashlib
import re
import uuid
from pathlib import Path
from typing import Tuple
from app.vendors.settings import Settings

SAFE_NAME_RE = re.compile(r"[^\w\-.·\u4e00-\u9fa5]")

def sanitize_filename(name: str) -> str:
    name = (name or "").strip().replace(" ", "_")
    name = SAFE_NAME_RE.sub("", name)
    return name or uuid.uuid4().hex

def split_name(name: str) -> Tuple[str, str]:
    p = Path(name)
    return p.stem, p.suffix

def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def atomic_move(src: Path, dst: Path) -> None:
    ensure_parent(dst)
    tmp_dst = dst.with_suffix(dst.suffix + ".tmp")
    if tmp_dst.exists():
        tmp_dst.unlink()
    src.replace(tmp_dst)
    tmp_dst.replace(dst)

def sha256_of_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(Settings.CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
