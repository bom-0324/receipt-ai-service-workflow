"""
media.py

영수증 파일 처리: 아이폰 사진(HEIC) 변환, 화면 미리보기, 증빙 사진 zip 만들기.
"""

import hashlib
import io
import re
import zipfile

HEIC_EXT = (".heic", ".heif")


def file_hash(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def prepare_upload(name: str, data: bytes) -> tuple[str, bytes, str]:
    """
    업로드 파일을 분석 가능한 형식으로 바꾼다.
    HEIC → JPG 변환. 반환: (파일명, 바이트, 오류메시지)
    """
    if not name.lower().endswith(HEIC_EXT):
        return name, data, ""
    try:
        from PIL import Image, ImageOps
        from pillow_heif import register_heif_opener

        register_heif_opener()
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        out = io.BytesIO()
        img.save(out, "JPEG", quality=92)
        return name.rsplit(".", 1)[0] + ".jpg", out.getvalue(), ""
    except ImportError:
        return name, data, f"{name}: HEIC 변환 패키지(pillow-heif)가 설치되어 있지 않습니다."
    except Exception as e:  # noqa: BLE001
        return name, data, f"{name}: HEIC 사진을 변환하지 못했습니다 ({e})"


def make_preview(name: str, data: bytes, max_side: int = 1600) -> bytes | None:
    """화면에 보여줄 이미지(JPEG). PDF는 첫 페이지를 그린다. 실패하면 None."""
    try:
        from PIL import Image, ImageOps

        if name.lower().endswith(".pdf"):
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(data)
            img = pdf[0].render(scale=2).to_pil()
        else:
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        img = img.convert("RGB")
        img.thumbnail((max_side, max_side))
        out = io.BytesIO()
        img.save(out, "JPEG", quality=88)
        return out.getvalue()
    except Exception:  # noqa: BLE001
        return None


def _safe(text, limit: int = 30) -> str:
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", str(text or "").strip()).strip("_")
    return s[:limit]


def evidence_filename(no: int, date, store, src_name: str) -> str:
    """엑셀 행 번호에 맞춘 증빙 파일명. 예) 01_2022-02-21_생선회관.jpg"""
    ext = "." + src_name.rsplit(".", 1)[-1].lower() if "." in src_name else ""
    parts = [f"{no:02d}", _safe(date, 10), _safe(store)]
    return "_".join(p for p in parts if p) + ext


def build_zip(items: list[tuple[str, bytes]]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for zip_name, data in items:
            z.writestr(zip_name, data)
    return out.getvalue()