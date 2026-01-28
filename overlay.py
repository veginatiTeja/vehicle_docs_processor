# overlay.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from PyPDF2 import PdfReader, PdfWriter
import io


def normalize_vin(vin):
    return vin.strip().upper().replace(" ", "") if vin else ""


def draw_vin_boxes(c, vin, start_x, y):
    vin = normalize_vin(vin)

    FONT_NAME = "Courier"
    FONT_SIZE = 10
    BOX_WIDTH = 16.0
    Y_OFFSET = -4.0

    c.setFont(FONT_NAME, FONT_SIZE)

    for i, ch in enumerate(vin):
        box_left = start_x + (i * BOX_WIDTH)
        char_width = stringWidth(ch, FONT_NAME, FONT_SIZE)
        x_centered = box_left + (BOX_WIDTH - char_width) / 2
        c.drawString(x_centered, y + Y_OFFSET, ch)


# ✅ MATCHES main.py CALL
def fill_vehicle_pdf(template_pdf, output_pdf, vehicle):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFont("Helvetica", 10)

    # ================= VEHICLE INFO =================
    if vehicle.get("year"):
        c.drawString(140, 685, vehicle["year"])

    if vehicle.get("make"):
        c.drawString(250, 685, vehicle["make"])

    if vehicle.get("model"):
        c.drawString(370, 685, vehicle["model"])

    # ================= VIN =================
    if vehicle.get("vin"):
        draw_vin_boxes(
            c,
            vehicle["vin"],
            start_x=123.0,
            y=635.0
        )

    # ================= TITLE =================
    if vehicle.get("title_no"):
        c.drawString(100, 555, vehicle["title_no"])

    if vehicle.get("title_state"):
        c.drawString(260, 555, vehicle["title_state"])

    # ================= ACQUISITION =================
    if vehicle.get("acq_date"):
        c.drawString(470, 450, vehicle["acq_date"])

    if vehicle.get("acq_from"):
        c.drawString(170, 450, vehicle["acq_from"])

    if vehicle.get("acq_address"):
        c.drawString(180, 423, vehicle["acq_address"])

    city_state_zip = []
    if vehicle.get("acq_city"):
        c.drawString(120, 398, vehicle["acq_city"])
    if vehicle.get("acq_state"):
        c.drawString(290, 398, vehicle["acq_state"])
    if vehicle.get("acq_zip"):
        c.drawString(380, 398, vehicle["acq_zip"])

    c.save()
    packet.seek(0)

    # ================= MERGE WITH TEMPLATE =================
    overlay_pdf = PdfReader(packet)
    template = PdfReader(template_pdf)
    writer = PdfWriter()

    page = template.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)
