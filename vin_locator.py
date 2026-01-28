import pdfplumber

def detect_vin_position(template_pdf):
    """
    Detect VIN start X and Y based on 'Vehicle Ident. No.'
    """
    with pdfplumber.open(template_pdf) as pdf:
        page = pdf.pages[0]
        words = page.extract_words(use_text_flow=True)

        for w in words:
            txt = w["text"].lower()
            if "vehicle" in txt and "ident" in txt:
                label_end_x = w["x1"]

                # 🔧 measured once from template
                VIN_OFFSET_X = 18
                VIN_Y_OFFSET = -6

                vin_start_x = label_end_x + VIN_OFFSET_X
                vin_y = w["top"] + VIN_Y_OFFSET

                return round(vin_start_x, 2), round(vin_y, 2)

    raise Exception("VIN label not found in template")
