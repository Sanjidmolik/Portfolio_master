"""Secure file uploads.

* Images are opened with Pillow, size-capped and **re-encoded** (WebP, or PNG
  for tiny icons). Re-encoding strips EXIF/metadata and any payload hidden
  inside the original file. SVG is deliberately not accepted (script risk).
* Documents (CV) must be real PDFs (magic bytes checked).
* Files get random names; user-supplied filenames are never used on disk.
"""
from __future__ import annotations

import secrets
from pathlib import Path

from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}
Image.MAX_IMAGE_PIXELS = 40_000_000  # decompression-bomb guard


class UploadError(ValueError):
    pass


def _upload_dir(sub: str) -> Path:
    root = Path(current_app.config["UPLOAD_FOLDER"]) / sub
    root.mkdir(parents=True, exist_ok=True)
    return root


def _size(fs: FileStorage) -> int:
    fs.stream.seek(0, 2)
    size = fs.stream.tell()
    fs.stream.seek(0)
    return size


def save_image(fs: FileStorage, sub: str = "images", max_dim: int = 1920) -> str:
    """Validate + re-encode an uploaded image. Returns path relative to /static."""
    if not fs or not fs.filename:
        raise UploadError("No file selected.")
    ext = fs.filename.rsplit(".", 1)[-1].lower() if "." in fs.filename else ""
    if ext not in IMAGE_EXTS:
        raise UploadError("Images must be JPG, PNG, WebP or GIF.")
    if _size(fs) > current_app.config["MAX_IMAGE_BYTES"]:
        raise UploadError("Image is too large (max 6 MB).")
    try:
        with Image.open(fs.stream) as probe:
            probe.verify()
        fs.stream.seek(0)
        img = Image.open(fs.stream)
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise UploadError("That file is not a valid image.")

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "transparency" in img.info or img.mode in ("P", "LA") else "RGB")
    img.thumbnail((max_dim, max_dim))

    name = secrets.token_hex(12) + ".webp"
    dest = _upload_dir(sub) / name
    img.save(dest, "WEBP", quality=86, method=4)
    return f"uploads/{sub}/{name}"


def save_pdf(fs: FileStorage, sub: str = "documents") -> str:
    if not fs or not fs.filename:
        raise UploadError("No file selected.")
    if not fs.filename.lower().endswith(".pdf"):
        raise UploadError("The CV must be a PDF file.")
    if _size(fs) > current_app.config["MAX_DOCUMENT_BYTES"]:
        raise UploadError("PDF is too large (max 8 MB).")
    head = fs.stream.read(5)
    fs.stream.seek(0)
    if head != b"%PDF-":
        raise UploadError("That file is not a valid PDF.")
    name = secrets.token_hex(12) + ".pdf"
    dest = _upload_dir(sub) / name
    fs.save(dest)
    return f"uploads/{sub}/{name}"


def delete_upload(rel_path: str | None) -> None:
    """Delete a previously uploaded file (only inside the uploads folder)."""
    if not rel_path or not rel_path.startswith("uploads/"):
        return
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = (root.parent / rel_path).resolve()
    if root in target.parents and target.is_file():
        try:
            target.unlink()
        except OSError:
            current_app.logger.warning("Could not delete upload %s", rel_path)
