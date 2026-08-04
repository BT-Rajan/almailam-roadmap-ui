import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

settings = get_settings()

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".dwg", ".dxf",
    ".jpg", ".jpeg", ".png", ".txt", ".csv",
}


def _safe_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationAppError(
            f"File type '{suffix or 'unknown'}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return suffix


def save_upload(file: UploadFile, subdirectory: str) -> tuple[str, str, int]:
    """Returns (storage_key, original_filename, size_bytes). storage_key is
    a generated name -- the original filename is never used as a path
    component, so nothing in the client-supplied name (.., /, null bytes,
    etc.) can affect where the file ends up."""
    extension = _safe_extension(file.filename or "")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = file.file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise ValidationAppError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB upload limit.")
    if not contents:
        raise ValidationAppError("Uploaded file is empty.")

    directory = Path(settings.UPLOADS_DIR) / subdirectory
    directory.mkdir(parents=True, exist_ok=True)

    generated_name = f"{uuid.uuid4().hex}{extension}"
    destination = directory / generated_name
    destination.write_bytes(contents)

    storage_key = str(Path(subdirectory) / generated_name)
    return storage_key, (file.filename or generated_name), len(contents)


def resolve_path(storage_key: str) -> Path:
    path = (Path(settings.UPLOADS_DIR) / storage_key).resolve()
    uploads_root = Path(settings.UPLOADS_DIR).resolve()
    if uploads_root not in path.parents and path != uploads_root:
        raise ValidationAppError("Invalid file reference.")
    return path


def format_file_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
