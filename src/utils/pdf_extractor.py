import pdfplumber
import streamlit as st
from config.app_config import MAX_PDF_PAGES
from utils.validators import validate_pdf_file, validate_pdf_content


def extract_text_from_pdf(pdf_file) -> str:
    """Extract and validate text from an uploaded PDF file."""
    try:
        # Validate that the file is actually a PDF
        is_valid, error = validate_pdf_file(pdf_file)
        if not is_valid:
            return error

        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                return f"PDF exceeds the maximum page limit of {MAX_PDF_PAGES} pages."

            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if not text.strip():
            return (
                "Could not extract text from this PDF. "
                "Please ensure it is not a scanned image-only document."
            )

        # Validate that content looks like a blood report
        is_valid, error = validate_pdf_content(text)
        if not is_valid:
            return error

        return text

    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
