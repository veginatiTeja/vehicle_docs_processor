import re
import pytesseract
from pdf2image import convert_from_path

BUSINESS_KEYWORDS = {
    "AUTO", "AUTOS", "MOTOR", "MOTORS", "SALES",
    "LLC", "INC", "CORP", "COMPANY", "CO",
    "GROUP", "DEALER", "USED", "CAR", "VOLKSWAGEN"
}

KNOWN_COLORS = [
    "BLACK", "WHITE", "SILVER", "GRAY", "GREY", "BLUE", "RED",
    "GREEN", "YELLOW", "ORANGE", "BROWN", "GOLD", "BURGUNDY",
    "MAROON", "BEIGE", "TAN", "PURPLE"
]


# ---------------- SELLER HELPERS ---------------- #

def extract_invoice_seller(text):
    if "INVOICE TO BUYER" not in text:
        return None

    for line in text.splitlines():
        line = line.strip()
        if "AUTO SALES" in line or "VOLKSWAGEN" in line:
            parts = re.split(r"\s{2,}|\.", line)
            parts = [p.strip() for p in parts if len(p.strip()) > 4]
            if parts:
                return parts[0].title()
    return None


def is_valid_seller_name(text):
    if "," in text:
        return False

    words = text.split()
    if len(words) < 2 or len(words) > 7:
        return False

    for w in words:
        if not w.isalpha():
            return False

    return any(w.upper() in BUSINESS_KEYWORDS for w in words)


# ---------------- DATE ---------------- #

def extract_acquisition_date(text):
    patterns = [
        r"(SALE DATE|NEW SALE DATE)\s*[:\-]?\s*(\d{1,2}[-/][A-Z]{3}[-/]\d{4})",
        r"(ISSUE DATE)\s*[:\-]?\s*(\d{1,2}[-/][A-Z]{3}[-/]\d{4})",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(2)

    fallback = re.search(r"\b(\d{1,2}[-/][A-Z]{3}[-/]\d{4})\b", text)
    return fallback.group(1) if fallback else None


# ---------------- ODOMETER ---------------- #

def extract_odometer(text):
    patterns = [
        r"MILEAGE\s*[:\-]?\s*([\d,]{4,})\s*MILES",
        r"ODOMETER[^0-9]{0,15}([\d,]{4,})"
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return re.sub(r"[^\d]", "", m.group(1))
    return None


# ---------------- MAIN ---------------- #

def extract_vehicle_data_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    vehicles = []

    for page_no, image in enumerate(images, start=1):
        print(f"OCR page {page_no}")
        text = pytesseract.image_to_string(image)
        text_upper = text.upper()

        vin_match = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", text_upper)
        if not vin_match:
            continue

        vehicle = {"vin": vin_match.group(1)}

        # -------- YEAR / MAKE / MODEL -------- #
        ymm = re.search(r"\b(19\d{2}|20\d{2})[,\s]+([A-Z]{3,})[,\s]+([A-Z0-9]{3,})", text_upper)
        if ymm:
            vehicle["year"] = ymm.group(1)
            vehicle["make"] = ymm.group(2).title()
            if ymm.group(3) != vehicle["vin"]:
                vehicle["model"] = ymm.group(3).title()

        # -------- COLOR -------- #
        for c in KNOWN_COLORS:
            if re.search(rf"\b{c}\b", text_upper):
                vehicle["color"] = c.title()
                break

        # -------- TITLE -------- #
        title = re.search(r"TITLE STATE/NUMBER:\s*([A-Z]{2})/([A-Z0-9]+)", text_upper)
        if title:
            vehicle["title_state"] = title.group(1)
            vehicle["title_no"] = title.group(2)

        # -------- DATE -------- #
        acq_date = extract_acquisition_date(text_upper)
        if acq_date:
            vehicle["acq_date"] = acq_date

        # -------- SELLER BLOCK (PAGE 2 PRIORITY) -------- #
        seller_block = re.search(r"\bSELLER\b(.*?)(\bBUYER\b|$)", text_upper, re.S)
        if seller_block:
            block = seller_block.group(1)
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            seller_name = None

    # 1️⃣ Try strict business-name detection first
            for line in lines:
                if is_valid_seller_name(line):
                    seller_name = line.title()
                    break

    # 2️⃣ If not found, fallback: line before address
        addr_index = -1
        for i, line in enumerate(lines):
            if re.search(r"\d{3,}.*(ST|RD|AVE|TPKE|ROAD|STREET)", line):
                addr_index = i
                break

        if not seller_name and addr_index > 0:
            seller_name = lines[addr_index - 1].title()

        if seller_name:
            vehicle["acq_from"] = seller_name

    # -------- Address extraction (unchanged) --------
        addr = re.search(r"([0-9].+)\n([A-Z ]+),\s*([A-Z]{2})\s*(\d{5})", block)
        if addr:
            vehicle["acq_address"] = addr.group(1).title()
            vehicle["acq_city"] = addr.group(2).title()
            vehicle["acq_state"] = addr.group(3)
            vehicle["acq_zip"] = addr.group(4)

        # -------- INVOICE SELLER (PAGE 1 FALLBACK) -------- #
        if "acq_from" not in vehicle:
            invoice_seller = extract_invoice_seller(text_upper)
            if invoice_seller:
                vehicle["acq_from"] = invoice_seller

        # -------- ODOMETER -------- #
        odo = extract_odometer(text_upper)
        if odo:
            vehicle["acq_odometer_in"] = odo

        # -------- FLAGS -------- #
        vehicle["purchased_for_resale"] = "Yes"
        vehicle["held_on_consignment"] = "No"

        vehicles.append(vehicle)

    return vehicles
