import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def parse_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        text = page.get_text()
        full_text += text + "\n"
        
        # Scanned PDF Fallback
        if len(text.strip()) < 10:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            full_text += pytesseract.image_to_string(img) + "\n"
            
    return full_text