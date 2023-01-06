from django.db.models import Q, Count
from django.shortcuts import render

from apps.parameters.bin.core import get_in_progress
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import UpdateThirdpartynumForm


def purchase_without_suppliers(request):
    """Visualisation des intégrations sans Tiers Identifiés"""
    form = UpdateThirdpartynumForm(request.POST or None)
    context = {
        "titre_table": "Factures Intégrées sans Tiers X3",
        "elements_list": EdiImport.objects.filter(
            Q(third_party_num="") | Q(third_party_num__isnull=True)
        )
        .values("uuid_identification", "third_party_num", "flow_name", "supplier", "supplier_ident")
        .annotate(dcount=Count("uuid_identification")),
        "form": form,
        "margin_table": 50,
    }

    if get_in_progress():
        context["en_cours"] = True
        context["titre_table"] = "INTEGRATION EN COURS, PATIENTEZ..."

    return render(
        request, "validation_purchases/integration_without_third_party_num.html", context=context
    )
