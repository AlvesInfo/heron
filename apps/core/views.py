import pendulum

from django.shortcuts import render
from django.template.loader import render_to_string

from apps.edi.models import EdiImport


def pdf_view(request):
    context = {
        "maison": EdiImport.objects.filter(
            sale_invoice=True, big_category="f2dda460-20db-4b05-8bb8-fa80a1ff146b"
        ),
        "invoice_date": pendulum.today().date(),
    }
    content = render_to_string("core/marchandises.html", context)

    with open(
        "C:\\SitesWeb\\heron\\your-template-static.html", "w", encoding="utf8"
    ) as static_file:
        static_file.write(content)

    return render(request, "core/marchandises.html", context)
