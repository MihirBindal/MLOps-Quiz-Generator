import docx

def parse_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    # Join all paragraphs with a newline
    return "\n".join([para.text for para in doc.paragraphs])