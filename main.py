import os
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

from extractor import extract_complete_vehicle_record
from overlay import create_overlay


def ocr_pdf(pdf_path):
    text = ""
    pages = convert_from_path(pdf_path, dpi=300)
    for i, page in enumerate(pages):
        print(f"OCR page {i+1}")
        text += pytesseract.image_to_string(page)
    return text


def merge_overlay(template_pdf, overlay_pdf, output_pdf):
    template = PdfReader(template_pdf)
    overlay = PdfReader(overlay_pdf)

    page = template.pages[0]
    page.merge_page(overlay.pages[0])

    writer = PdfWriter()
    writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


if __name__ == "__main__":
    input_pdf = "input_docs/sample.pdf"
    template_pdf = "templates/used_vehicle_record_template.pdf"

    os.makedirs("output", exist_ok=True)

    text = ocr_pdf(input_pdf)
    vehicles = extract_complete_vehicle_record(text)

    for idx, vehicle in enumerate(vehicles, 1):
        overlay_pdf = f"output/overlay_{idx}.pdf"
        final_pdf = f"output/used_vehicle_{vehicle['year']}_{vehicle['make']}_{vehicle['model']}.pdf"

        create_overlay(vehicle, overlay_pdf)
        merge_overlay(template_pdf, overlay_pdf, final_pdf)

        print("✅ Auto-filled PDF created:", final_pdf)

    print("\n🚗 Extracted Vehicle Data:")
    for v in vehicles:
        print(v)
