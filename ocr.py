import pytesseract
from PIL import Image

def extract_text_from_ticket(image):
    img= Image.open(image)
    text= pytesseract.image_to_string(img)
    return text