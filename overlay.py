from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

VIN_BOX_WIDTH = 16

def draw_vin_boxes_centered(c, vin, start_x, y):
    for i, ch in enumerate(vin):
        x = start_x + (i * VIN_BOX_WIDTH)
        c.drawCentredString(x + VIN_BOX_WIDTH / 2, y, ch)

def create_overlay(vehicle, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=letter)
    c.setFont("Helvetica", 9)

    # ---- IDENTIFICATION ----
    if vehicle.get("year"):
        c.drawString(140, 685, vehicle["year"])
    if vehicle.get("make"):
        c.drawString(250, 685, vehicle["make"])
    if vehicle.get("model"):
        c.drawString(370, 685, vehicle["model"])
    if vehicle.get("color"):
        c.drawString(520, 685, vehicle["color"])

    # ---- VIN ----
    if vehicle.get("vin"):
        draw_vin_boxes_centered(c, vehicle["vin"], start_x=130, y=632)

    # ---- ENGINE ----
    if vehicle.get("engine"):
        c.drawString(430, 620, vehicle["engine"])

    # ---- TITLE ----
    if vehicle.get("title_no"):
        c.drawString(100, 555, vehicle["title_no"])
    if vehicle.get("title_state"):
        c.drawString(260, 555, vehicle["title_state"])

    # ---- ACQUISITION ----
    if vehicle.get("acq_from"):
        c.drawString(110, 470, vehicle["acq_from"])
    if vehicle.get("acq_date"):
        c.drawString(400, 470, vehicle["acq_date"])
    if vehicle.get("mileage"):
        c.drawString(480, 430, vehicle["mileage"])

    c.save()
