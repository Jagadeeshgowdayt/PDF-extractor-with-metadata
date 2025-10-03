"""
Copyright (c) 2025 Jagadeeshgowdayt
This file is part of PDF-extractor-with-metadata, released under the MIT License.
See LICENSE in the project root for details.
"""

import os
import hashlib
import requests
from typing import Optional, Dict, Any, List
from io import BytesIO
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
try:
    from PIL import Image
except ImportError:
    Image = None


def download_pdf(url: str, dest_path: str, session: Optional[requests.Session] = None) -> str:
    """Download PDF from url to dest_path. Returns dest_path."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    s = session or requests
    resp = s.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)
    return dest_path


def file_checksum(path: str, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf_metadata(path: str) -> Dict[str, Any]:
    """Return basic metadata from PDF file using PyMuPDF if available."""
    meta = {}
    if fitz is None:
        return meta
    try:
        doc = fitz.open(path)
        meta = doc.metadata or {}
        meta["page_count"] = doc.page_count
        doc.close()
    except Exception:
        pass
    return meta


def pdf_to_jpegs(pdf_path: str, out_dir: str, prefix: str, quality: int = 85, max_size_kb: int = 100) -> List[str]:
    """Convert each page of pdf to JPEG using PyMuPDF, compress to <=max_size_kb. Returns list of image paths."""
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is required for conversion")
    if Image is None:
        raise RuntimeError("Pillow is required for JPEG compression")
    os.makedirs(out_dir, exist_ok=True)
    img_paths = []
    doc = fitz.open(pdf_path)
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        # Save to memory first
        img_bytes = pix.tobytes("ppm")
        pil_img = Image.open(BytesIO(img_bytes))
        # Compress to <=max_size_kb
        for q in range(85, 10, -5):
            buf = BytesIO()
            pil_img.save(buf, format="JPEG", quality=q, optimize=True)
            size_kb = buf.tell() // 1024
            if size_kb <= max_size_kb:
                break
        # If still too large, resize and try again
        while buf.tell() // 1024 > max_size_kb and pil_img.width > 200:
            pil_img = pil_img.resize((pil_img.width // 2, pil_img.height // 2), Image.LANCZOS)
            buf = BytesIO()
            pil_img.save(buf, format="JPEG", quality=60, optimize=True)
        # Save to disk
        img_name = f"{prefix}_{i+1}.jpeg"
        img_path = os.path.join(out_dir, img_name)
        with open(img_path, "wb") as f:
            f.write(buf.getvalue())
        img_paths.append(img_path)
    doc.close()
    return img_paths
