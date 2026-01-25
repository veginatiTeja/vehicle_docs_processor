# from pypdf import PdfReader

# reader = PdfReader("templates/used_vehicle_form.pdf")
# fields = reader.get_fields()

# for name in fields:
#     print(name)

from pypdf import PdfReader

reader = PdfReader("templates/used_vehicle_form.pdf")

for page in reader.pages:
    if "/Annots" in page:
        for annot in page["/Annots"]:
            field = annot.get_object()
            print(
                field.get("/T"),
                field.get("/V"),
                field.get("/FT"),
            )
