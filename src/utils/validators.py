import re
import filetype


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if bool(re.match(pattern, email)):
        return True, ""
    return False, "Invalid email format."


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    return True, ""


def validate_pdf_file(file) -> tuple[bool, str]:
    """Validate that the uploaded file is a valid PDF using magic bytes."""
    try:
        # Read the first few bytes to detect file type
        header = file.read(261)
        file.seek(0)
        kind = filetype.guess(header)
        if kind is None or kind.mime != "application/pdf":
            return False, "Uploaded file is not a valid PDF. Please upload a PDF file."
        return True, ""
    except Exception as e:
        return False, f"Unable to validate file: {str(e)}"


def validate_pdf_content(text: str) -> tuple[bool, str]:
    """
    Validate that the extracted PDF text looks like a medical blood report
    by checking for common medical keywords.
    """
    if not text or len(text.strip()) < 50:
        return False, "The PDF appears to be empty or too short to be a blood report."

    medical_keywords = [
        "blood", "hemoglobin", "glucose", "cholesterol", "wbc", "rbc",
        "platelet", "creatinine", "bilirubin", "albumin", "report",
        "laboratory", "lab", "test", "result", "normal", "range",
        "mg", "dl", "g/dl", "u/l", "mmol", "µl", "hba1c", "triglyceride",
        "ldl", "hdl", "alt", "ast", "tsh", "ferritin"
    ]

    text_lower = text.lower()
    matches = sum(1 for keyword in medical_keywords if keyword in text_lower)

    if matches < 3:
        return (
            False,
            "This does not appear to be a medical blood report. "
            "Please upload a valid blood test report."
        )
    return True, ""
