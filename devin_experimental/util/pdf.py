"""PDF utilities."""


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """
    Count the number of pages in a PDF from bytes.

    Parameters
    ----------
    pdf_bytes : bytes
        Raw PDF file content.

    Returns
    -------
    int
        Number of pages in the PDF.
    """
    try:
        import pypdfium2 as pdfium
    except Exception as e:
        raise RuntimeError("pypdfium2 is required for PDF page counting. Install it with: pip install pypdfium2") from e

    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        return len(doc)
    finally:
        doc.close()
