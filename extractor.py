import re

INVALID_WORDS = {
    "make", "model", "year", "state", "title",
    "vehicle", "record", "information", "any", "no"
}

def clean_word(word):
    if not word:
        return None
    word = word.strip(",.:; ")
    if word.lower() in INVALID_WORDS:
        return None
    if len(word) < 3:
        return None
    return word


def extract_complete_vehicle_record(text):
    vehicles = []

    # 🚫 Ignore blank USED VEHICLE RECORD template page
    if "USED VEHICLE RECORD" in text.upper():
        text = text.split("USED VEHICLE RECORD")[0]

    blocks = re.split(
        r"VEHICLE INFORMATION|Vehicle Information|BILL OF SALE|Invoice",
        text,
        flags=re.I
    )

    for block in blocks:
        vehicle = {}

        # ---------------- YEAR / MAKE / MODEL ----------------
        ym = re.search(
            r"\b(19\d{2}|20\d{2})[, ]+([A-Za-z]{3,})[, ]+([A-Za-z]{3,})",
            block
        )
        if ym:
            year = ym.group(1)
            make = clean_word(ym.group(2))
            model = clean_word(ym.group(3))
            if make and model:
                vehicle["year"] = year
                vehicle["make"] = make
                vehicle["model"] = model

        # ---------------- VIN (MANDATORY) ----------------
        vin = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", block)
        if vin:
            vehicle["vin"] = vin.group(0)

        # ---------------- ENGINE ----------------
        engine = re.search(r"\b(\d+[- ]?Cylinder|V6|V8)\b", block, re.I)
        if engine:
            vehicle["engine"] = engine.group(1)

        # ---------------- COLOR ----------------
        color = re.search(
            r"\b(Black|White|Silver|Gray|Blue|Red|Green|Burgundy|Yellow)\b",
            block,
            re.I
        )
        if color:
            vehicle["color"] = color.group(1)

        # ---------------- MILEAGE ----------------
        mileage = re.search(r"Odometer[:\s]*([\d,]+)|Mileage[:\s]*([\d,]+)", block, re.I)
        if mileage:
            vehicle["mileage"] = (mileage.group(1) or mileage.group(2)).replace(",", "")

        # ---------------- TITLE INFO ----------------
        title = re.search(
            r"Title\s*(State|Information).*?([A-Z]{2})\s*[/\-]\s*([A-Z0-9]{5,})",
            block,
            re.I
        )
        if title:
            vehicle["title_state"] = title.group(2)
            vehicle["title_no"] = title.group(3)

        # ================= ACQUISITION SECTION =================

        # -------- ACQUISITION DATE --------
        date = re.search(
            r"(Purchase Date|Acquired On|Transaction Date | Sale date)[:\s]*([\d/]{8,10})",
            block,
            re.I
        )
        if date:
            vehicle["acq_date"] = date.group(2)

        # -------- SELLER (HEADER ONLY – SAFE) --------
        seller_block = re.search(
            r"SELLER\s*:\s*\n([A-Z][A-Z &.,'-]{3,})",
            text
        )
        if seller_block:
            seller = seller_block.group(1).strip()

            # Hard safety filter
            if not re.search(r"(authorized|representative|bill|tax|payment)", seller, re.I):
                vehicle["acq_from"] = seller

        # -------- SELLER ADDRESS --------
        address_block = re.search(
            r"SELLER\s*:.*?\n.*?\n([0-9]{1,5}\s[A-Z0-9\s.,'-]+)\n([A-Z\s]+,\s[A-Z]{2}\s[0-9]{5})",
            text,
            re.S
        )
        if address_block:
            vehicle["acq_address"] = (
                address_block.group(1).strip() + ", " +
                address_block.group(2).strip()
            )

        # ---------------- FINAL VALIDATION ----------------
        if {"vin", "year", "make", "model"} <= vehicle.keys():
            vehicles.append(vehicle)

    return vehicles
