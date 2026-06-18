"""
Document signature verification using PyMuPDF.
Checks that an admin-uploaded Return & Deposit Agreement PDF contains a
handwritten/scanned signature (detected as an embedded image).
"""
import fitz  # PyMuPDF


def verify_signature(pdf_path: str) -> bool:
    """
    Returns True if the PDF contains at least one embedded image on any page.
    Handwritten/scanned signatures appear as image objects in PDFs.
    Returns False if no images are found (document likely unsigned)
    or if the file cannot be opened.
    """
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            if page.get_images(full=False):
                doc.close()
                return True
        doc.close()
        return False
    except Exception as exc:
        print(f"[SignatureVerify] error reading PDF: {exc}")
        return False
