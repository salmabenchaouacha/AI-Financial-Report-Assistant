import os
import tempfile
from contextlib import contextmanager

import cloudinary
import cloudinary.uploader
import requests


def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
        api_key=os.environ.get("CLOUDINARY_API_KEY"),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def upload_pdf_to_cloud(local_path: str, public_id: str) -> str:
    configure_cloudinary()
    result = cloudinary.uploader.upload(
        local_path,
        resource_type="raw",
        public_id=public_id,
        overwrite=True,
        type="upload",
    )
    return result["secure_url"]


def download_to_temp(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f:
        f.write(response.content)
    return tmp_path


@contextmanager
def local_copy_of(doc):
    if doc.path.startswith("http"):
        tmp_path = download_to_temp(doc.path)
        try:
            yield tmp_path
        finally:
            os.remove(tmp_path)
    else:
        yield doc.path