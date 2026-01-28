from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io


FIELD_POSITIONS = {
    "vin": (100, 650),
    "year": (100, 630),
    "make": (200, 630),
    "model": (300, 630),
    "mileage": (200, 610),

    "acq_from": (100, 560),
    "acq_address": (100, 540),
    "acq_city": (100, 520),
    "acq_state": (260, 520),
    "acq_zip": (320, 520),

    "purchased_for_resale": (100, 480),
    "held_on_consignment": (260, 480),
}


def fill_vehicle_pdf(template_pdf, output_pdf, data):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    for field, (x, y) in FIELD_POSITIONS.items():
        if field in data:
            can.drawString(x, y, str(data[field]))

    can.save()
    packet.seek(0)

    overlay_pdf = PdfReader(packet)
    base_pdf = PdfReader(template_pdf)
    writer = PdfWriter()

    page = base_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)
