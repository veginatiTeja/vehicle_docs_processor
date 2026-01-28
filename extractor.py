import re

# ---------------- CONSTANTS ----------------

INVALID_WORDS = {
    "any", "year", "make", "model", "vehicle",
    "information", "number", "state", "title",
    "invoice", "bill", "sale", "and", "of", "the"
}

INVALID_SELLERS = [
    "auction", "transactions", "seller purchaser",
    "authorized representative", "terms and conditions",
    "transferor", "buyer", "purchaser"
]

COLORS = [
    "Black", "White", "Silver", "Gray", "Grey",
    "Blue", "Red", "Green", "Burgundy", "Yellow"
]


# ---------------- HELPERS ----------------

def clean_word(word):
    if not word:
        return None
    w = word.strip(",.:; ").title()
    if w.lower() in INVALID_WORDS or len(w) < 3:
        return None
    return w


# ---------------- MAIN EXTRACTION ----------------

def extract_vehicle_from_page(text):
    vehicle = {}

    # ---------- VIN (MANDATORY ANCHOR) ----------
    vin = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", text)
    if not vin:
        return None
    vehicle["vin"] = vin.group(0)

    # ---------- YEAR / MAKE / MODEL (FORMAT 1) ----------
    ym = re.search(
        r"\b(19\d{2}|20\d{2})\s*,?\s*([A-Z]{3,})\s*,?\s*([A-Z0-9]{3,})",
        text,
        re.I
    )
    if ym:
        vehicle["year"] = ym.group(1)
        vehicle["make"] = clean_word(ym.group(2))
        vehicle["model"] = clean_word(ym.group(3))

    # ---------- YEAR ----------
    year = re.search(r"\bYear[:\s]+(19\d{2}|20\d{2})", text, re.I)
    if year:
        vehicle["year"] = year.group(1)

    # ---------- MAKE ----------
    make = re.search(r"\bMake[:\s]+([A-Za-z]{3,})", text, re.I)
    if make:
        vehicle["make"] = clean_word(make.group(1))

    # ---------- MODEL ----------
    model = re.search(r"\bModel[:\s]+([A-Za-z0-9]{2,})", text, re.I)
    if model:
        vehicle["model"] = clean_word(model.group(1))

    # ---------- MAKE FALLBACK (fixes Jeep=None) ----------
    if not vehicle.get("make"):
        make_alt = re.search(
            r"\b(19\d{2}|20\d{2})\s*,?\s*([A-Z]{3,})\s*,",
            text,
            re.I
        )
        if make_alt:
            vehicle["make"] = make_alt.group(2).title()

    # ---------- BLOCK VIN AS MODEL ----------
    if vehicle.get("model") and re.fullmatch(r"[A-HJ-NPR-Z0-9]{11,}", vehicle["model"], re.I):
        del vehicle["model"]

    # ---------- COLOR ----------
    for c in COLORS:
        if re.search(rf"\b{c}\b", text, re.I):
            vehicle["color"] = c
            break

    # ---------- ENGINE ----------
    engine = re.search(r"\b(V6|V8|\d+\s*Cylinder)\b", text, re.I)
    if engine:
        vehicle["engine"] = engine.group(1)

    # ---------- MILEAGE ----------
    mileage = re.search(r"(Mileage|Odometer).*?([\d,]{3,})", text, re.I)
    if mileage:
        vehicle["mileage"] = mileage.group(2).replace(",", "")

    # ---------- TITLE (FINAL SAFE VERSION) ----------
    title = re.search(
        r"(Title State/Number|State:)\s*[:\-]?\s*([A-Z]{2})\s*(?:/|Number:)?\s*([A-Z0-9]{5,})",
        text,
        re.I
    )
    if title:
        title_no = title.group(3)
        if not title_no.lower().startswith("number"):
            vehicle["title_state"] = title.group(2)
            vehicle["title_no"] = title_no

    # ---------- SELLER + ADDRESS (STRICT) ----------
    seller = re.search(
        r"\bSeller\b\s*\n\s*([A-Z][A-Z0-9 .,&'-]{5,50})",
        text,
        re.I
    )

    if seller:
        s = seller.group(1).strip()
        if not any(bad in s.lower() for bad in INVALID_SELLERS):
            vehicle["acq_from"] = s

            # Address ONLY if seller exists
            address = re.search(
                r"\bSeller\b.*?\n[A-Z0-9 .,&'-]+\n([0-9].+)\n([A-Z ]+),\s*([A-Z]{2})\s*(\d{5})",
                text,
                re.S
            )
            if address:
                vehicle["acq_address"] = address.group(1).strip()
                vehicle["acq_city"] = address.group(2).title()
                vehicle["acq_state"] = address.group(3)
                vehicle["acq_zip"] = address.group(4)

    # ---------- TRANSACTION DATE ----------
    date = re.search(
        r"(Sale Date|Issue Date|Printed on|dated)\s*[:\-]?\s*([0-9]{1,2}[-/][A-Za-z]{3}[-/][0-9]{4}|[0-9]{2}/[0-9]{2}/[0-9]{2,4})",
        text,
        re.I
    )
    if date:
        vehicle["acq_date"] = date.group(2)

    # ---------- BUSINESS DEFAULTS ----------
    vehicle["purchased_for_resale"] = "Yes"
    vehicle["held_on_consignment"] = "No"

    return vehicle
