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


def is_central_mass_auction(text):
    return "CENTRAL MASS. AUTO AUCTION" in text.upper()


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


# ================== SELLER EXTRACTORS ==================

def extract_carmax_seller(text):
    m = re.search(r'CarMax\s*-\s*([A-Z\s]+)', text, re.I)
    if not m:
        return None
    return {"acq_from": f"CarMax - {m.group(1).title()}"}


def extract_manheim_seller(text):
    m = re.search(
        r'Seller\s*\n\s*(.*?)\n\s*(\d{2,5}.*?)\n\s*([A-Z\s]+),\s*([A-Z]{2})\s*(\d{5})',
        text,
        re.S | re.I
    )
    if not m:
        return None

    return {
        "acq_from": clean_text(m.group(1)).title(),
        "acq_address": clean_text(m.group(2)).title(),
        "acq_city": clean_text(m.group(3)).title(),
        "acq_state": m.group(4).upper(),
        "acq_zip": m.group(5),
    }


def extract_adesa_page1_seller(text):
    m = re.search(r'Invoice to Buyer\s+(.*?)\n', text, re.I)
    if not m:
        return None

    line = m.group(1)
    seller = line.split('.')[0] if '.' in line else line
    return seller.strip().title()


# ================== MODEL FALLBACK ==================

def extract_fuzzy_model(text):
    """
    Handles OCR corruption like:
    'Mode}! Passat' → Passat
    """
    m = re.search(r'MOD[A-Z\W]{1,5}\s*([A-Z]{3,})', text)
    if m:
        return m.group(1).title()
    return None

# ================= TITLE STATE & TITLE NUMBER =================

import re

def extract_title_info(text):
    text = text.upper()

    title_state = None
    title_no = None

    # Pattern 1: "TITLE STATE/NUMBER MA BM759181"
    m1 = re.search(
        r"(TITLE STATE/NUMBER|TITLE INFORMATION|STATE:)\s*[:\-]?\s*"
        r"([A-Z]{2})\s*[/\-]?\s*([A-Z0-9]{5,})",
        text,
        re.I
    )
    print("m1 ",m1)
  
    if m1:
        ts = m1.group(2)
        tn = m1.group(3)

        # ✅ title number MUST contain at least one digit
        if re.search(r"\d", tn):
            return ts, tn

    # Pattern 2: "TITLE NO: BM759181"
    m2 = re.search(
        r"\bTITLE\s*(NO|NUMBER|#)?\s*[:\-]?\s*([A-Z0-9]{6,})\b",
        text,
        re.I
    )

    print("m2 ",m2)

    if m2:
        tn = m2.group(2)

        # ❌ reject words like NUMBER, TITLE, etc.
        if re.search(r"\d", tn):
            return None, tn

    return None, None

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

        ymm_comma = re.search(
            r"\b(19\d{2}|20\d{2})\s*,\s*([A-Z]{3,})\s*,\s*([A-Z0-9]{3,})",
            text_upper
        )

        ymm_space = re.search(
            r"\b(19\d{2}|20\d{2})\s+([A-Z]{3,})\s+([A-Z0-9]{3,})",
            text_upper
        )

        ymm_labeled = re.search(
            r"YEAR\s*(19\d{2}|20\d{2}).*?MAKE\s*([A-Z]{3,}).*?MODEL\s*([A-Z0-9]{3,})",
            text_upper,
            re.S
        )

        ymm = ymm_comma or ymm_space or ymm_labeled

        if ymm:
            vehicle["year"] = ymm.group(1)
            vehicle["make"] = ymm.group(2).title()
            if len(ymm.group(3)) < 12:
                vehicle["model"] = ymm.group(3).title()

        # -------- FUZZY MODEL FALLBACK --------
        if "model" not in vehicle:
            fuzzy_model = extract_fuzzy_model(text_upper)
            if fuzzy_model:
                vehicle["model"] = fuzzy_model

        # -------- COLOR --------
        color = extract_color(text_upper)
        if color:
            vehicle["color"] = color

        # -------- TITLE -------- #
        title_state, title_no = extract_title_info(text_upper)
        if title_no:
            vehicle["title_no"] = title_no

        if title_state:
            vehicle["title_state"] = title_state


        # -------- DATE --------
        acq_date = extract_acquisition_date(text_upper)
        if acq_date:
            vehicle["acq_date"] = acq_date

        # -------- SELLER PRIORITY --------
        seller = extract_carmax_seller(text)
        if seller:
            vehicle.update(seller)

        elif not is_central_mass_auction(text):
            seller = extract_manheim_seller(text)
            if seller:
                vehicle.update(seller)
            else:
                seller_name = extract_adesa_page1_seller(text)
                if seller_name:
                    vehicle["acq_from"] = seller_name

        # -------- ODOMETER --------
        odo = extract_odometer(text_upper)
        if odo:
            vehicle["acq_odometer_in"] = odo

        # -------- FLAGS --------
        vehicle["purchased_for_resale"] = "Yes"
        vehicle["held_on_consignment"] = "No"

        vehicles.append(vehicle)

    return vehicles
