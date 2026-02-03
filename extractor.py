import re
import pytesseract
from pdf2image import convert_from_path

# ================== HELPERS ==================

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


KNOWN_COLORS = [
    "BLACK", "WHITE", "SILVER", "GRAY", "GREY", "BLUE", "RED",
    "GREEN", "YELLOW", "ORANGE", "BROWN", "GOLD",
    "BURGUNDY", "MAROON", "BEIGE", "TAN", "PURPLE"
]


# ================== BASIC EXTRACTORS ==================

def extract_color(text):
    for c in KNOWN_COLORS:
        if re.search(rf"\b{c}\b", text):
            return c.title()
    return None


def extract_acquisition_date(text):
    m = re.search(r"\b(\d{1,2}[-/][A-Z]{3}[-/]\d{4})\b", text)
    return m.group(1) if m else None


def extract_odometer(text):
    patterns = [
        r"MILEAGE\s*[:\-]?\s*([\d,]{4,})",
        r"ODOMETER[^0-9]{0,20}([\d,]{4,})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return re.sub(r"[^\d]", "", m.group(1))
    return None


# ================== FUZZY MODEL ==================

def extract_fuzzy_model(text):
    m = re.search(r'MOD[A-Z\W]{1,5}\s*([A-Z]{3,})', text)
    if m:
        return m.group(1).title()
    return None


# ================= TITLE DETAILS =================

def extract_title_info(text):
    text = text.upper()

    # TITLE STATE + NUMBER
    m1 = re.search(
        r"(TITLE STATE/NUMBER|TITLE INFORMATION|STATE)\s*[:\-]?\s*"
        r"([A-Z]{2})\s*[/\-]?\s*([A-Z0-9]{5,})",
        text
    )
    if m1 and re.search(r"\d", m1.group(3)):
        return m1.group(2), m1.group(3)

    # TITLE NUMBER ONLY
    m2 = re.search(r"\bTITLE\s*(NO|NUMBER|#)?\s*[:\-]?\s*([A-Z0-9]{6,})\b", text)
    if m2 and re.search(r"\d", m2.group(2)):
        return None, m2.group(2)

    return None, None


# ================== GENERIC ACQUISITION ==================



import re

def extract_acquisition_details(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    text_u = text.upper()
    result = {}

    # ---------------- DATE ----------------
    m = re.search(r"\b(\d{1,2}[-/][A-Z]{3}[-/]\d{4})\b", text_u)
    if m:
        result["acq_date"] = m.group(1)

    # ---------------- ODOMETER ----------------
    m = re.search(r"(MILEAGE|ODOMETER)[^0-9]{0,20}([\d,]{4,})", text_u)
    if m:
        result["acq_odometer_in"] = re.sub(r"[^\d]", "", m.group(2))

    # ---------------- CITY / STATE / ZIP ----------------
    city = state = zipc = None
    for line in lines:
        m = re.search(r"([A-Z ]+),\s*([A-Z]{2})\s*(\d{5})", line.upper())
        if m:
            city = m.group(1).title()
            state = m.group(2)
            zipc = m.group(3)
            result["acq_city"] = city
            result["acq_state"] = state
            result["acq_zip"] = zipc
            break

    # ---------------- STREET ADDRESS ----------------
    for line in lines:
        lu = line.upper()
        if re.match(r"\d{1,6}\s+[A-Z0-9 ]+", lu):
            if any(w in lu for w in ["SALE", "DATE", "AUCTION", "INVOICE", "ODOMETER"]):
                continue
            if re.search(r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b", lu):
                continue
            if 2 <= len(line.split()) <= 6:
                result["acq_address"] = line.title()
                break

    # ---------------- ACQ_FROM (ROBUST) ----------------
    header = lines[:25]

    manheim_found = False
    region_words = []

    for line in header:
        cu = line.upper()

        if "MANHEIM" in cu:
            manheim_found = True

        if manheim_found:
            if "NEW" in cu:
                region_words.append("New")
            if "ENGLAND" in cu:
                region_words.append("England")

    if manheim_found:
        if region_words:
            result["acq_from"] = "Manheim " + " ".join(dict.fromkeys(region_words))
        else:
            result["acq_from"] = "Manheim"
        return result

    # --------- FALLBACK AUCTIONS ---------
    for line in header:
        cu = line.upper()
        if "ADESA" in cu:
            result["acq_from"] = line.title()
            break
        if "CENTRAL MASS" in cu:
            result["acq_from"] = "Central Mass. Auto Auction"
            break

    return result if result else None


# ================== MAIN PIPELINE ==================

def extract_vehicle_data_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    vehicles = []

    for page_no, image in enumerate(images, start=1):
        print(f"OCR page {page_no}")
        text = pytesseract.image_to_string(image)
        text_upper = text.upper()

        # -------- VIN --------
        vin_match = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", text_upper)
        if not vin_match:
            continue

        vehicle = {"vin": vin_match.group(1)}

        # -------- YEAR / MAKE / MODEL --------
        ymm = (
            re.search(r"\b(19\d{2}|20\d{2})\s*,\s*([A-Z]{3,})\s*,\s*([A-Z0-9]{3,})", text_upper)
            or re.search(r"\b(19\d{2}|20\d{2})\s+([A-Z]{3,})\s+([A-Z0-9]{3,})", text_upper)
            or re.search(
                r"YEAR\s*(19\d{2}|20\d{2}).*?MAKE\s*([A-Z]{3,}).*?MODEL\s*([A-Z0-9]{3,})",
                text_upper,
                re.S,
            )
        )

        if ymm:
            vehicle["year"] = ymm.group(1)
            vehicle["make"] = ymm.group(2).title()
            if len(ymm.group(3)) < 12:
                vehicle["model"] = ymm.group(3).title()

        if "model" not in vehicle:
            fm = extract_fuzzy_model(text_upper)
            if fm:
                vehicle["model"] = fm

        # -------- COLOR --------
        color = extract_color(text_upper)
        if color:
            vehicle["color"] = color

        # -------- TITLE --------
        title_state, title_no = extract_title_info(text_upper)
        if title_no:
            vehicle["title_no"] = title_no
        if title_state:
            vehicle["title_state"] = title_state

        # -------- ACQUISITION (GENERIC) --------
        acq = extract_acquisition_details(text)
        if acq:
            vehicle.update(acq)

        # -------- FLAGS --------
        vehicle["purchased_for_resale"] = "Yes"
        vehicle["held_on_consignment"] = "No"

        vehicles.append(vehicle)

    return vehicles
