from django.shortcuts import render
from django.template.loader import render_to_string


def pdf_view(request):
    context = range(10)
    content = render_to_string('clients_invoices/marchandises.html', context)

    with open('path/to/your-template-static.html', 'w') as static_file:
        static_file.write(content)

    return render(request, 'clients_invoices/marchandises.html', context)
