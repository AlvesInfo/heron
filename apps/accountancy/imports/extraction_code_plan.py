# pylint: disable=
"""
FR : Mise à jour des code plan sage par extraction depuis la table AccountSage et après sa
     mise à jour depuis fichier ZBI exporter depuis Sage X3
EN : Update of sage code plan by extraction from the AccountSage table and after its update from ZBI
     file export from Sage X3

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
from django.db.models import Count
from apps.accountancy.models import AccountSage, CodePlanSage


def update_code_plan():
    """Update de la table CodePlanSage, pour le foreign key dans les clients des centrales"""
    code_plan = (
        AccountSage.objects.values("code_plan_sage")
        .annotate(nb_plan=Count("code_plan_sage"))
        .order_by("code_plan_sage")
        .values_list("code_plan_sage", flat=True)
    )

    for plan in code_plan:
        CodePlanSage.objects.update_or_create(
            code_plan_sage=plan,
        )


if __name__ == "__main__":
    update_code_plan()
