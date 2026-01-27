# # overlay.py
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter

# FIELD_COORDS = {
#     "year": (140, 685),
#     "make": (250, 685),
#     "model": (370, 685),
#     "color": (520, 685),

#     "vin": (135, 620),
#     "engine": (430, 620),

#     "title_no": (100, 555),
#     "title_state": (260, 555),

#     "mileage": (480, 430),
# }

# def create_overlay_pdf(output_pdf, vehicle):
#     c = canvas.Canvas(output_pdf, pagesize=letter)
#     c.setFont("Helvetica", 10)

#     for field, (x, y) in FIELD_COORDS.items():
#         value = vehicle.get(field)
#         if value:                   # ✅ only print if value exists
#             c.drawString(x, y, str(value))

#     c.save()

# overlay.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth


def normalize_vin(vin):
    return vin.strip().upper().replace(" ", "") if vin else ""


def draw_vin_boxes(c, vin, start_x, y):
    """
    Draw VIN characters centered inside scanned | | boxes
    WITHOUT spacing drift
    """

    vin = normalize_vin(vin)

    FONT_NAME = "Courier"
    FONT_SIZE = 10
    BOX_WIDTH = 16.0          # actual box width on template
    Y_OFFSET = -4.0           # baseline correction

    c.setFont(FONT_NAME, FONT_SIZE)

    for i, ch in enumerate(vin):
        box_left = start_x + (i * BOX_WIDTH)
        char_width = stringWidth(ch, FONT_NAME, FONT_SIZE)

        # ✅ true center of box
        x_centered = box_left + (BOX_WIDTH - char_width) / 2
        c.drawString(x_centered, y + Y_OFFSET, ch)


def create_overlay(vehicle, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=letter)
    c.setFont("Helvetica", 10)

    # ===== HEADER =====
    if vehicle.get("year"):
        c.drawString(140, 685, vehicle["year"])
    if vehicle.get("make"):
        c.drawString(250, 685, vehicle["make"])
    if vehicle.get("model"):
        c.drawString(370, 685, vehicle["model"])
    if vehicle.get("color"):
        c.drawString(520, 685, vehicle["color"])

    # ===== VIN =====
    if vehicle.get("vin"):
        draw_vin_boxes(
            c,
            vehicle["vin"],
            start_x=123.0,   # first box LEFT edge
            y=635.0
        )

    # ===== ENGINE =====
    if vehicle.get("engine"):
        c.drawString(430, 620, vehicle["engine"])

    # ===== TITLE =====
    if vehicle.get("title_no"):
        c.drawString(100, 555, vehicle["title_no"])
    if vehicle.get("title_state"):
        c.drawString(260, 555, vehicle["title_state"])

    # ===== MILEAGE =====
    if vehicle.get("mileage"):
        c.drawString(480, 430, vehicle["mileage"])

    c.save()
