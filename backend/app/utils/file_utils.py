import os
import uuid

def safe_filename(original: str) -> str:
    ext = os.path.splitext(original)[1].lower()
    return f"{uuid.uuid4()}{ext}"

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
