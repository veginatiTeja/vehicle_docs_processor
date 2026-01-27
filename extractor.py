# extractor.py
import re

def extract_vehicles(text):
    vehicles = []

    blocks = re.split(r"VEHICLE INFORMATION|Vehicle Information", text, flags=re.I)

    for block in blocks:
        vehicle = {}

        # YEAR MAKE MODEL
        ym = re.search(r"\b(19\d{2}|20\d{2})[, ]+([A-Za-z]+)[, ]+([A-Za-z]+)", block)
        if ym:
            vehicle["year"] = ym.group(1)
            vehicle["make"] = ym.group(2)
            vehicle["model"] = ym.group(3)

        # VIN (MANDATORY)
        vin = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", block)
        if vin:
            vehicle["vin"] = vin.group(0)

        # TITLE INFO (Page 1 or Page 2)
        title = re.search(
            r"(Title State/Number|Title Information|State:)\s*[:\-]?\s*([A-Z]{2})\s*[/\-]?\s*([A-Z0-9]{5,})",
            block,
            re.I
        )
        if title:
            vehicle["title_state"] = title.group(2)
            vehicle["title_no"] = title.group(3)

        # MILEAGE
        mileage = re.search(r"Mileage[:\s]+([\d,]+)", block, re.I)
        if mileage:
            vehicle["mileage"] = mileage.group(1).replace(",", "")

        # ENGINE
        engine = re.search(r"(\d+[-\s]?Cylinder)", block, re.I)
        if engine:
            vehicle["engine"] = engine.group(1)

        # VALID VEHICLE = MUST HAVE VIN
        if "vin" in vehicle:
            vehicles.append(vehicle)

    return vehicles
