import re
import pytesseract
from pdf2image import convert_from_path


BUSINESS_KEYWORDS = {
    "AUTO", "AUTOS", "MOTOR", "MOTORS", "SALES",
    "LLC", "INC", "CORP", "COMPANY", "CO",
    "GROUP", "DEALER", "USED", "CAR"
}


def is_valid_seller_name(text):
    if "," in text:
        return False

    words = text.split()

    # Word count rule
    if len(words) < 2 or len(words) > 5:
        return False

    # Each word must be meaningful
    for w in words:
        if len(w) < 3:
            return False
        if not w.isalpha():
            return False

    # Must contain business keyword
    if not any(w.upper() in BUSINESS_KEYWORDS for w in words):
        return False

    return True


def extract_vehicle_data_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    vehicles = []

    for page_no, image in enumerate(images, start=1):
        print(f"OCR page {page_no}")
        text = pytesseract.image_to_string(image)
        text_upper = text.upper()

        vehicle = {}

        # ---------------- VIN ----------------
        vin_match = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", text_upper)
        if not vin_match:
            continue

        vin = vin_match.group(1)
        vehicle["vin"] = vin

        # ---------------- YEAR / MAKE / MODEL ----------------
        ymm = re.search(
            r"\b(19\d{2}|20\d{2})\s+([A-Z]{3,})\s+([A-Z0-9]{3,})",
            text_upper
        )
        if ymm:
            vehicle["year"] = ymm.group(1)
            vehicle["make"] = ymm.group(2).title()

            model = ymm.group(3)
            if model != vin:
                vehicle["model"] = model.title()

        # ---------------- MILEAGE ----------------
        mileage = re.search(r"MILEAGE[:\s]+([\d,]{3,})", text_upper)
        if mileage:
            vehicle["mileage"] = mileage.group(1).replace(",", "")

        # ---------------- ACQUISITION DATE ----------------
        date = re.search(r"\b(\d{1,2}-[A-Z]{3}-\d{4})\b", text_upper)
        if date:
            vehicle["acq_date"] = date.group(1)

        # ---------------- SELLER BLOCK ----------------
        seller_block = re.search(
            r"\bSELLER\b(.*?)(\bBUYER\b|$)",
            text_upper,
            re.S
        )

        if seller_block:
            block = seller_block.group(1)

            for line in block.splitlines():
                clean = line.strip()
                if is_valid_seller_name(clean):
                    vehicle["acq_from"] = clean.title()
                    break

            address = re.search(
                r"([0-9].+)\n([A-Z ]+),\s*([A-Z]{2})\s*(\d{5})",
                block
            )
            if address:
                vehicle["acq_address"] = address.group(1).title()
                vehicle["acq_city"] = address.group(2).title()
                vehicle["acq_state"] = address.group(3)
                vehicle["acq_zip"] = address.group(4)

        # ---------------- DEFAULT FLAGS ----------------
        vehicle["purchased_for_resale"] = "Yes"
        vehicle["held_on_consignment"] = "No"

        vehicles.append(vehicle)

    return vehicles
