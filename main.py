import os
from extractor import extract_vehicle_data_from_pdf
from overlay import fill_vehicle_pdf

INPUT_PDF = "input_docs/sample.pdf"
TEMPLATE_PDF = "templates/used_vehicle_record_template.pdf"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

vehicles = extract_vehicle_data_from_pdf(INPUT_PDF)

print("\n🚗 Extracted Vehicle Data:")

for idx, vehicle in enumerate(vehicles, start=1):
    print(vehicle)

    year = vehicle.get("year", "YYYY")
    make = vehicle.get("make", "UNKNOWN")
    model = vehicle.get("model", "MODEL")

    output_path = f"{OUTPUT_DIR}/used_vehicle_page_{idx}_{year}_{make}_{model}.pdf"

    fill_vehicle_pdf(
        TEMPLATE_PDF,
        output_path,
        vehicle
    )

    print(f"✅ Auto-filled PDF created: {output_path}")
