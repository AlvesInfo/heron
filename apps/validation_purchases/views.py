from django.shortcuts import render

# Create your views here.


def controles_exports(requests):
    context = {"titre_table": "Contrôle Exports"}
    return render(requests, "controles/controles_exports.html")
