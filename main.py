import os
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

from extractor import extract_vehicle_from_page
from overlay import create_overlay


def ocr_pdf_pages(pdf_path):
    pages_text = []
    pages = convert_from_path(pdf_path, dpi=300)

    for i, page in enumerate(pages):
        print(f"OCR page {i + 1}")
        text = pytesseract.image_to_string(page)
        pages_text.append((i + 1, text))

    return pages_text


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

    pages = ocr_pdf_pages(input_pdf)
    vehicles = []

    for page_no, text in pages:
        vehicle = extract_vehicle_from_page(text)

        if not vehicle:
            continue

        vehicles.append(vehicle)

        year = vehicle.get("year", "YYYY")
        make = vehicle.get("make") or "UNKNOWN"
        model = vehicle.get("model") or "MODEL"


        overlay_pdf = f"output/overlay_page_{page_no}.pdf"
        output_pdf = f"output/used_vehicle_page_{page_no}_{year}_{make}_{model}.pdf"

        create_overlay(vehicle, overlay_pdf)
        merge_overlay(template_pdf, overlay_pdf, output_pdf)

        print("✅ Auto-filled PDF created:", output_pdf)

    print("\n🚗 Extracted Vehicle Data:")
    for v in vehicles:
        print(v)
