import re

INVALID_WORDS = {
    "any", "year", "make", "model", "vehicle",
    "information", "number", "state", "title",
    "invoice", "bill", "sale", "and", "of", "the"
}

COLORS = [
    "Black", "White", "Silver", "Gray", "Grey",
    "Blue", "Red", "Green", "Burgundy", "Yellow"
]

def clean_word(word):
    if not word:
        return None
    w = word.strip(",.:; ").title()
    if w.lower() in INVALID_WORDS:
        return None
    if len(w) < 3:
        return None
    return w


def extract_vehicle_from_page(text):
    """
    Extract ONE vehicle from ONE OCR page
    """
    vehicle = {}

    # ---------- VIN (anchor – must exist) ----------
    vin = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", text)
    if not vin:
        return None
    vehicle["vin"] = vin.group(0)

    # ---------- FORMAT 1: VEHICLE INFORMATION ----------
    ym = re.search(
        r"\b(19\d{2}|20\d{2})\s*,?\s*([A-Za-z]{3,})\s*,?\s*([A-Za-z]{3,})",
        text
    )
    if ym:
        vehicle["year"] = ym.group(1)
        vehicle["make"] = clean_word(ym.group(2))
        vehicle["model"] = clean_word(ym.group(3))

    # ---------- FORMAT 2: LABELLED YEAR / MAKE / MODEL ----------
    if "year" not in vehicle:
        year = re.search(r"\bYear[:\s]+(19\d{2}|20\d{2})", text, re.I)
        if year:
            vehicle["year"] = year.group(1)

    if "make" not in vehicle:
        make = re.search(r"\bMake[:\s]+([A-Za-z]{3,})", text, re.I)
        if make:
            vehicle["make"] = clean_word(make.group(1))

    if "model" not in vehicle:
        model = re.search(r"\bModel[:\s]+([A-Za-z0-9]{2,})", text, re.I)
        if model:
            vehicle["model"] = clean_word(model.group(1))

    # ---------- FORMAT 3: INVOICE SUBJECT ----------
    subject = re.search(
        r"Subject\s+(19\d{2}|20\d{2})\s+([A-Za-z]{3,})\s+([A-Za-z0-9]+)",
        text,
        re.I
    )
    if subject:
        vehicle["year"] = subject.group(1)
        vehicle["make"] = clean_word(subject.group(2))
        vehicle["model"] = clean_word(subject.group(3))

    # ---------- COLOR ----------
    for c in COLORS:
        if re.search(rf"\b{c}\b", text, re.I):
            vehicle["color"] = c
            break

    # ---------- ENGINE ----------
    engine = re.search(r"\b(V6|V8|\d+\s*Cylinder)\b", text, re.I)
    if engine:
        vehicle["engine"] = engine.group(1)

    # ---------- MILEAGE / ODOMETER ----------
    mileage = re.search(
        r"(Mileage|Odometer)\s*[:\s]+([\d,]+)",
        text,
        re.I
    )
    if mileage:
        vehicle["mileage"] = mileage.group(2).replace(",", "")

    # ---------- TITLE STATE + NUMBER ----------
    title = re.search(
        r"(Title State/Number|Title Information|State:)\s*[:\-]?\s*([A-Z]{2})\s*[/\-]?\s*([A-Z0-9]{5,})",
        text,
        re.I
    )
    if title:
        vehicle["title_state"] = title.group(2)
        vehicle["title_no"] = title.group(3)

    # ---------- ACQUISITION SOURCE ----------
    seller = re.search(
        r"(Seller|Purchased From|Obtained From)\s*[:\-]?\s*([A-Z][A-Z0-9 .,&'-]{5,40})",
        text
    )
    if seller:
        s = seller.group(2).strip()
        if not re.search(r"(authorized|representative|bill|tax|payment)", s, re.I):
            vehicle["acq_from"] = s

    return vehicle


def extract_complete_vehicle_record(pages_text):
    """
    pages_text = list of OCR text (one per page)
    """
    vehicles = []

    for idx, page_text in enumerate(pages_text, 1):
        vehicle = extract_vehicle_from_page(page_text)
        if vehicle:
            vehicles.append(vehicle)

    return vehicles
