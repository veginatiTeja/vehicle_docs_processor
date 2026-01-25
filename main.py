# import os
# from pdf2image import convert_from_path
# import pytesseract

# # Explicit path (safe on Windows)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# def extract_text_ocr(pdf_path):
#     full_text = ""

#     images = convert_from_path(pdf_path, dpi=300)

#     for page_number, img in enumerate(images, start=1):
#         print("OCR page", page_number)
#         text = pytesseract.image_to_string(img, lang="eng")

#         if text and text.strip():
#             full_text += f"\n--- PAGE {page_number} ---\n"
#             full_text += text
#         else:
#             full_text += f"\n--- PAGE {page_number} ---\n[NO TEXT FOUND]\n"

#     return full_text


# if __name__ == "__main__":

#     pdf_path = "samples/sample.pdf"
#     os.makedirs("output", exist_ok=True)

#     text = extract_text_ocr(pdf_path)

#     print(text)

#     with open("output/raw_text.txt", "w", encoding="utf-8") as f:
#         f.write(text)

#     print("\n✅ OCR text extraction completed.")


import os
import re
from pdf2image import convert_from_path
import pytesseract
from pypdf import PdfReader, PdfWriter
import time   
from pypdf.generic import NameObject, BooleanObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_ocr(pdf_path):
    full_text = ""
    images = convert_from_path(pdf_path, dpi=300)

    for page_number, img in enumerate(images, start=1):
        print("OCR page", page_number)
        text = pytesseract.image_to_string(img, lang="eng")
        full_text += f"\n--- PAGE {page_number} ---\n{text}"

    return full_text


# -------- FIELD EXTRACTION -------- #

def extract_vehicles(text):
    vehicles = []

    blocks = re.split(r"VEHICLE INFORMATION", text, flags=re.IGNORECASE)

    for block in blocks[1:]:
        vehicle = {}

        ym_match = re.search(
            r"(\d{4})[, ]+([A-Z][A-Za-z]+)[, ]+([A-Z][A-Za-z]+)",
            block
        )
        if ym_match:
            vehicle["year"] = ym_match.group(1)
            vehicle["make"] = ym_match.group(2)
            vehicle["model"] = ym_match.group(3)

        vin_match = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", block)
        if vin_match:
            vehicle["vin"] = vin_match.group(0)

        mileage_match = re.search(r"Mileage[:\s]+([\d,]+)", block, re.I)
        if mileage_match:
            vehicle["mileage"] = mileage_match.group(1).replace(",", "")

        engine_match = re.search(r"(\d+[-\s]?Cylinder)", block, re.I)
        if engine_match:
            vehicle["engine"] = engine_match.group(1)

        # ✅ Validation filter
        if "vin" in vehicle and vehicle.get("make", "").lower() != "make":
            vehicles.append(vehicle)

    # ✅ return AFTER loop
    return vehicles

def fill_vehicle_pdf(template_pdf, output_pdf, vehicle):
    reader = PdfReader(template_pdf)
    writer = PdfWriter()

    # Copy pages
    for page in reader.pages:
        writer.add_page(page)

    # ✅ Correct way to attach AcroForm
    if reader.trailer["/Root"].get("/AcroForm"):
        writer._root_object[NameObject("/AcroForm")] = reader.trailer["/Root"]["/AcroForm"]
        writer._root_object[NameObject("/AcroForm")][NameObject("/NeedAppearances")] = BooleanObject(True)

    # Fill form fields
    writer.update_page_form_field_values(
        writer.pages[0],
        {
            "vehicle_year": vehicle.get("year", ""),
            "vehicle_make": vehicle.get("make", ""),
            "vehicle_model": vehicle.get("model", ""),
            "vehicle_vin": vehicle.get("vin", ""),
            "vehicle_mileage": vehicle.get("mileage", ""),
            "vehicle_engine": vehicle.get("engine", ""),
        }
    )

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print("✅ Auto-filled PDF generated:", output_pdf)

def flatten_pdf(filled_pdf, final_pdf):
    reader = PdfReader(filled_pdf)
    page = reader.pages[0]

    c = canvas.Canvas(final_pdf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica", 10)

    for annot in page.get("/Annots", []):
        field = annot.get_object()

        if field.get("/FT") == "/Tx" and field.get("/V"):
            value = str(field.get("/V"))

            rect = field.get("/Rect")
            x = rect[0]
            y = rect[1]

            c.drawString(x + 2, y + 4, value)

    c.save()
    print("✅ Flattened PDF created:", final_pdf)

def hard_flatten_pdf(filled_pdf, final_pdf, vehicle):
    c = canvas.Canvas(final_pdf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica", 11)

    y = height - 80
    x_label = 60
    x_value = 220

    fields = [
        ("Vehicle Year", vehicle.get("year", "")),
        ("Vehicle Make", vehicle.get("make", "")),
        ("Vehicle Model", vehicle.get("model", "")),
        ("VIN", vehicle.get("vin", "")),
        ("Mileage", vehicle.get("mileage", "")),
        ("Engine", vehicle.get("engine", "")),
    ]

    for label, value in fields:
        c.drawString(x_label, y, label + ":")
        c.drawString(x_value, y, str(value))
        y -= 40

    c.save()
    print("✅ HARD-FLATTENED PDF CREATED:", final_pdf)

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject

def autofill_used_vehicle_form(template_pdf, output_pdf, vehicle):
    reader = PdfReader(template_pdf)
    writer = PdfWriter()

    # ✅ THIS IS CRITICAL
    writer.clone_document_from_reader(reader)

    # ✅ Force appearance regeneration
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    # ✅ Fill text fields
    writer.update_page_form_field_values(
        writer.pages[0],
        {
            "model_year": vehicle.get("year", ""),
            "make": vehicle.get("make", ""),
            "model": vehicle.get("model", ""),
            "vin": vehicle.get("vin", ""),
        }
    )

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print("✅ Auto-filled PDF created:", output_pdf)




if __name__ == "__main__":

    pdf_path = "samples/sample.pdf"
    os.makedirs("output", exist_ok=True)

    ocr_text = extract_text_ocr(pdf_path)

    vehicles = extract_vehicles(ocr_text)


    # if vehicles:
    #     filled_pdf = f"output/used_vehicle_filled_{int(time.time())}.pdf"
    #     final_pdf = f"output/used_vehicle_final_{int(time.time())}.pdf"
    #     autofill_used_vehicle_form(
    #     "templates/used_vehicle_form.pdf",
    #     filled_pdf,
    #     vehicles[0]
    # )
    
    for index, vehicle in enumerate(vehicles, start=1):
        safe_make = vehicle.get("make", "UNKNOWN").replace(" ", "_")
        safe_model = vehicle.get("model", "UNKNOWN").replace(" ", "_")
        safe_year = vehicle.get("year", "YYYY")
        
        output_pdf = (
        f"output/used_vehicle_{index}_"
        f"{safe_year}_{safe_make}_{safe_model}.pdf"
    )
        autofill_used_vehicle_form(
        "templates/used_vehicle_form.pdf",
        output_pdf,
        vehicle
    )


    # flatten_pdf(filled_pdf, final_pdf)

    print("\n🚗 Extracted Vehicles:")
    for v in vehicles:
        print(v)

    with open("output/vehicles.json", "w", encoding="utf-8") as f:
        import json
        json.dump(vehicles, f, indent=2)

    # print("\n✅ Day-3 vehicle extraction completed.")



