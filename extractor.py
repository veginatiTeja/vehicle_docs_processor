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


def extract_invoice_seller(text):
    """
    Extract seller from auction invoice header (Invoice to Buyer pages)
    """
    if "INVOICE TO BUYER" not in text:
        return None

    for line in text.splitlines():
        line = line.strip()
        if "AUTO SALES" in line or "VOLKSWAGEN" in line:
            parts = re.split(r"\s{2,}|\.", line)
            parts = [p.strip() for p in parts if len(p.strip()) > 5]
            if parts:
                return parts[0].title()

    return None


def is_valid_seller_name(text):
    if "," in text:
        return False

    words = text.split()
    if len(words) < 2 or len(words) > 6:
        return False

    for w in words:
        if not w.isalpha():
            return False

    return any(w.upper() in BUSINESS_KEYWORDS for w in words)


def extract_acquisition_date(text):
    """
    Priority:
    1. Sale Date
    2. Issue / Issued Date
    3. Fallback generic date (last resort)
    """
    patterns = [
        r"(SALE DATE|SALE\s*DT)\s*[:\-]?\s*(\d{1,2}[-/][A-Z]{3}[-/]\d{4})",
        r"(ISSUE DATE|DATE ISSUED)\s*[:\-]?\s*(\d{1,2}[-/][A-Z]{3}[-/]\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(2)

    # Fallback – ONLY if invoice-specific date not found
    fallback = re.search(r"\b(\d{1,2}[-/][A-Z]{3}[-/]\d{4})\b", text)
    if fallback:
        return fallback.group(1)

    return None


# -----------------------------
def extract_odometer(text):
    print("Text ",text)
    patterns = [
    # ADESA header style: Odometer: 91,839 Miles
    r"ODOMETER\s*[:\-]?\s*([\d,]{4,})\s*MILES",

    # MILEAGE: 93464 MILES
    r"MILEAGE\s*[:\-]?\s*([\d,]{4,})\s*MILES",

    # OCR noisy variants
    r"ODOMETER[^0-9]{0,15}([\d,]{4,})",
    r"MILEAGE[^0-9]{0,15}([\d,]{4,})",
]


    for p in patterns:
        m = re.search(p, text)
        print("m after regex ",m)
        if m:
            return re.sub(r"[^\d]", "", m.group(1))

    return None


def extract_odometer_near_vin(text):
    """
    Try to extract odometer appearing on the same line
    or nearby the VIN (common in ADESA invoices)
    """
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if "VIN:" in line or "VIN" in line:
            # check same line
            m = re.search(r"([\d,]{4,})\s*MILES", line)
            if m:
                return m.group(1).replace(",", "")

            # check next 2 lines
            for j in range(i + 1, min(i + 3, len(lines))):
                m = re.search(r"([\d,]{4,})\s*MILES", lines[j])
                if m:
                    return m.group(1).replace(",", "")
    return None



def extract_vehicle_data_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    vehicles = []

    for page_no, image in enumerate(images, start=1):
        print(f"OCR page {page_no}")

        text = pytesseract.image_to_string(image)
        text_upper = text.upper()

        vehicle = {}

        # ---------- VIN ----------
        vin_match = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", text_upper)
        if not vin_match:
            continue

        vehicle["vin"] = vin_match.group(1)

        # ---------- YEAR / MAKE / MODEL ----------
        ymm = re.search(
            r"\b(19\d{2}|20\d{2})[,\s]+([A-Z]{3,})[,\s]+([A-Z0-9]{3,})",
            text_upper
        )
        if ymm:
            vehicle["year"] = ymm.group(1)
            vehicle["make"] = ymm.group(2).title()
            model = ymm.group(3)
            if model != vehicle["vin"]:
                vehicle["model"] = model.title()

        # -------------------------
        # COLOR extraction
        # -------------------------
        color = None

        # 1️⃣ Look for explicit COLOR field
        m = re.search(r"COLOR[:\s]*([A-Z ]{3,20})", text_upper)
        if m:
            candidate = m.group(1).strip()
            for c in KNOWN_COLORS:
                if c in candidate:
                    color = c.title()
                    break

        # 2️⃣ Search anywhere for known colors
        if not color:
            for c in KNOWN_COLORS:
                if re.search(rf"\b{c}\b", text_upper):
                    color = c.title()
                    break

        # 3️⃣ Vehicle info comma-based fallback
        
        if not color:
            m = re.search(r"\d{4}[\s,]+[A-Z]+[\s,]+[A-Z0-9]+[\s,]+([A-Z]+)[\s,]", text_upper)
            if m and m.group(1) in KNOWN_COLORS:
                color = m.group(1).title()

        if color:
            vehicle["color"] = color


        # ---------- TITLE ----------
        title = re.search(r"TITLE STATE/NUMBER:\s*([A-Z]{2})/([A-Z0-9]+)", text_upper)
        if title:
            vehicle["title_state"] = title.group(1)
            vehicle["title_no"] = title.group(2)

        # ---------- ACQUISITION DATE ----------
        acq_date = extract_acquisition_date(text_upper)
        if acq_date:
            vehicle["acq_date"] = acq_date

        # ---------- SELLER (Invoice Header) ----------
        seller = extract_invoice_seller(text_upper)
        if seller:
            vehicle["acq_from"] = seller

        # ---------- SELLER BLOCK ----------
        seller_block = re.search(
            r"\bSELLER\b(.*?)(\bBUYER\b|$)",
            text_upper,
            re.S
        )

        if seller_block and "acq_from" not in vehicle:
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


           # ---- ODOMETER (Vehicle Info → Acquisition) ----
        
        
        odometer = extract_odometer(text_upper)

       # Fallback: VIN-adjacent odometer (ADESA style)
        if not odometer:
            odometer = extract_odometer_near_vin(text_upper)
        
        if odometer and "acq_odometer_in" not in vehicle:
            vehicle["acq_odometer_in"] = odometer
        # ---------- FLAGS ----------
        vehicle["purchased_for_resale"] = "Yes"
        vehicle["held_on_consignment"] = "No"

        vehicles.append(vehicle)

    return vehicles