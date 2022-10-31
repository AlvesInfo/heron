from django.shortcuts import render

# Create your views here.


def sage_controls_sales(requests):
    context = {"titre_table": "Contrôle Intégration Sage X3 - Ventes"}
    return render(requests, "validation_sales/sage_controls.html")
