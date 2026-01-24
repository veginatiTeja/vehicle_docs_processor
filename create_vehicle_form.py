from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os


OUTPUT_PDF = "templates/used_vehicle_form.pdf"


def create_used_vehicle_form():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    width, height = A4
    form = c.acroForm

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "USED VEHICLE RECORD")
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        width / 2,
        height - 70,
        "Motor Vehicle / Part Identification & History"
    )

    y = height - 120
    x_label = 50
    x_field = 200
    field_width = 300
    field_height = 18

    # ---------------- TEXT FIELDS ---------------- #

    fields = [
        ("Model Year", "model_year"),
        ("Make", "make"),
        ("Model", "model"),
        ("Color", "color"),
        ("Description of Part", "description"),
        ("Vehicle Identification No. (VIN)", "vin"),
        ("Engine No.", "engine_no"),
        ("Reg. No. (if any)", "reg_no"),
        ("Title No.", "title_no"),
        ("State", "state"),
        ("Describe Changes (if any)", "altered_description"),
    ]

    for label, name in fields:
        c.drawString(x_label, y, label + ":")
        form.textfield(
            name=name,
            x=x_field,
            y=y - 4,
            width=field_width,
            height=field_height,
            borderStyle="underlined",
            forceBorder=True,
        )
        y -= 35

    # ---------------- YES / NO CHECKBOX ---------------- #

    c.drawString(
        x_label,
        y,
        "Have any of these numbers been altered, amended, or defaced?"
    )

    form.checkbox(
        name="altered_yes",
        x=x_field,
        y=y - 5,
        size=15,
        buttonStyle="check",
        forceBorder=True
    )
    c.drawString(x_field + 20, y, "Yes")

    form.checkbox(
        name="altered_no",
        x=x_field + 80,
        y=y - 5,
        size=15,
        buttonStyle="check",
        forceBorder=True
    )
    c.drawString(x_field + 100, y, "No")

    y -= 40

    # ---------------- SALVAGE TITLE CHECKBOXES ---------------- #

    c.setFont("Helvetica-Bold", 11)
    c.drawString(
        x_label,
        y,
        'If this is a Salvage Title, check all "brands" that apply:'
    )
    c.setFont("Helvetica", 11)
    y -= 25

    brands = [
        "repairable",
        "parts_only",
        "collision",
        "fire",
        "flood",
        "salt_water_flood",
        "theft",
        "vandalism",
        "reconstructed",
        "prior_owner_retained",
        "recovered_theft",
        "odometer_discrepancy",
        "other",
    ]

    x = x_label
    for brand in brands:
        form.checkbox(
            name=brand,
            x=x,
            y=y - 5,
            size=14,
            buttonStyle="check",
            forceBorder=True
        )
        c.drawString(x + 18, y, brand.replace("_", " ").title())
        x += 180

        if x > width - 180:
            x = x_label
            y -= 25

    c.save()
    print("✅ used_vehicle_form.pdf created successfully")


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    create_used_vehicle_form()
