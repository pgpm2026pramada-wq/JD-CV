"""Text extraction from uploaded files (PDF, DOCX, TXT) for the Streamlit app."""
from __future__ import annotations

import io
import re


def _clean(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001
            continue
    return _clean("\n".join(parts))


def _extract_docx(data: bytes) -> str:
    import docx  # python-docx

    document = docx.Document(io.BytesIO(data))
    return _clean("\n".join(p.text for p in document.paragraphs))


def _extract_txt(data: bytes) -> str:
    return _clean(data.decode("utf-8", errors="replace"))


def extract_text(filename: str, data: bytes) -> str:
    """Extract plain text from an uploaded file's bytes."""
    name = (filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""

    if ext == "pdf":
        return _extract_pdf(data)
    if ext == "docx":
        return _extract_docx(data)
    if ext == "txt":
        return _extract_txt(data)
    if ext == "doc":
        text = _clean(re.sub(r"[^\x09\x0A\x0D\x20-\x7E]+", " ", _extract_txt(data)))
        if len(re.sub(r"\s", "", text)) < 40:
            raise ValueError(
                "Legacy .doc files can't be read reliably. Please re-save as .docx, "
                "PDF, or TXT, or paste the text directly."
            )
        return text
    # Unknown — best effort.
    return _extract_txt(data)
