try:
    import pymupdf as fitz
except ImportError:
    import fitz
from docx import Document
import io

def extract_text_with_pages(file_bytes: bytes, file_type: str) -> list[dict]:
    """
    ගොනුව කියවා [{"page_number": 1, "text": "..."}, ...] ලෙස ආපසු ලබා දෙයි.
    """
    pages_data = []

    if file_type == "pdf":
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            text = page.get_text("text").strip()
            if text:
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text
                })
        pdf_doc.close()

    elif file_type == "docx":
        doc = Document(io.BytesIO(file_bytes))
        full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

        if full_text:
            pages_data.append({
                "page_number": 1,
                "text": full_text
            })

    return pages_data