from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os


OUTPUT_PDF = "templates/used_vehicle_form.pdf"


def create_used_vehicle_form():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4) #Opens a new PDF document in memory
    print("canvas defintion result ",c)
    width, height = A4 #Used for positioning text & fields (595 * 842)
    form = c.acroForm   #Enables fillable PDF fields

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "USED VEHICLE RECORD") #draws text in horizontally centered 50 points down from top
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        width / 2,
        height - 70,
        "Motor Vehicle / Part Identification & History"  #smaller subtles places slightly below title
    )

    print("canvas after setting titles and subtles ",c)

    #layout positioning variables
    y = height - 120  #current vertical position moves from downward 722
    x_label = 50   # X position for text labels
    x_field = 200   # X position for input fields
    field_width = 300   # width of text fields
    field_height = 18    #height of text fields

    # ---------------- TEXT FIELDS ---------------- #

    print("y ",y)
    fields = [
        ("Model Year", "model_year"),
        ("Make", "make"),
        ("Model", "model"),
        ("Color", "color"),
        ("Description of Part", "description"),
        ("Vehicle Identification No", "vin"),
        # ("Engine No.", "engine_no"),
        # ("Reg. No. (if any)", "reg_no"),
        ("Title No", "title_no"),
        ("State", "state"),
        ("Describe Changes (if any)", "altered_description"),
    ]    #label shown to user and internal fields name

    for label, name in fields:   #runs once per each field
        print("label in loop ",label,"name in loop ",name,"x ",x_field,"y ",y)
        c.drawString(x_label, y, label + ":")  #draws visble label 
        form.textfield(
            name=name,
            x=x_field,
            y=y - 6,
            width=field_width,
            height=field_height,
            borderStyle="underlined",
            forceBorder=True,
        )  #create fillable text field
        y -= 35  #creates vertical spacing adjusts this to tighter/loosen layout

    # ---------------- YES / NO CHECKBOX ---------------- #
 
   
    print("x_label ",x_label, "y ",y)
    c.drawString(
        x_label,
        y,
        "Have any of these numbers been altered, amended, or defaced?"
    )

    print("x_field ",x_field, "y ",y)

    form.checkbox(
        name="altered_yes",
        x=x_field,
        y=y-25,
        size=15,
        buttonStyle="check",
        forceBorder=True
    )

    print("x field + 20 ", x_field + 20, "y ",y)
    c.drawString(x_field + 18 , y-20, "Yes")

    print("x_field ",x_field, "y ",y)

    form.checkbox(
        name="altered_no",
        x=x_field + 80,
        y=y-25,
        size=15,
        buttonStyle="check",
        forceBorder=True
    )

    print("x field + 100 ", x_field + 20, "y ",y)

    c.drawString(x_field+100, y-20, "No")

    y -= 40

    # ---------------- SALVAGE TITLE CHECKBOXES ---------------- #

    print("y before title checkboxes ",y)
    c.setFont("Helvetica-Bold", 11)
    print("x_label and y before salvage title checkobozwx ",x_label,y)
    c.drawString(
        x_label,
        y,
        'If this is a Salvage Title, check all "brands" that apply:'
    )
    c.setFont("Helvetica", 11)
    y -= 25

    print("y after title checkboxes ",y)

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
        print("x and y in formation of checkboxes  ",x,y)

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
            y -= 30

    c.save()
    print("✅ used_vehicle_form.pdf created successfully")


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    create_used_vehicle_form()
