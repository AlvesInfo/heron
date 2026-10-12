"""FR : Module des génération des RFA.

EN : RFA Generation Module.

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""

from uuid import UUID

from django.db import connection, transaction
from django.db.models import Q

from apps.book.models import Society
from apps.core.functions.functions_dates import last_day_month
from apps.edi.models import EdiValidation
from apps.rfa.sql_files.sql_rfa import SQL_INSERTION_ICON, SQL_RFA_INSERTION


class RfaPeriodError(Exception):
    """Aucune période de facturation ouverte : la génération des RFA est impossible."""


def get_open_period():
    """Retourne la période de facturation ouverte (EdiValidation non finalisée), ou None."""
    return EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()


def get_sql_kwargs(supplier_origin: str, period_rfa: str, uuid_identification: UUID):
    """Retourne le dictionnaire des arguments de la requête.

    :param supplier_origin: Fournisseur dont il faut générer les RFA
    :param period_rfa: Période de RFA à refacturer
    :param uuid_identification: uuid_identification de la trace
    :return:
    """
    period = get_open_period()

    if period is None:
        raise RfaPeriodError(
            "Aucune période de facturation ouverte : génération des RFA impossible"
        )

    last_day = last_day_month(period.billing_period)
    society = Society.objects.get(third_party_num=supplier_origin)

    return {
        "uuid_identification": uuid_identification,
        "third_party_num": society.third_party_num,
        "supplier": f"{society.short_name} RFA",
        # Identifiant fournisseur de la centrale, vide s'il n'est pas renseigné
        "supplier_ident": (society.centers_suppliers_indentifier or "").split("|", maxsplit=1)[0],
        "supplier_name": society.short_name,
        "siret_payeur": f"{society.short_name} RFA",
        "invoice_number": (f"{supplier_origin}_{str(last_day.month).zfill(2)}_{last_day.year!s}_"),
        "invoice_date": last_day.isoformat(),
        "reference_article": period_rfa,
        "libelle": (f"RFA {society.short_name} {str(last_day.month).zfill(2)}/{last_day.year!s}"),
        "familly": "AA",
        "vat_rate": "550",
        "vat": "002",
        "flow_name": "rfa_flow",
    }


@transaction.atomic
def insert_rfa(supplier_origin: str, period_rfa: str, uuid_identification: UUID):
    """Génération des RFA.

    :param supplier_origin: Fournisseur dont il faut générer les RFA
    :param period_rfa: Période de RFA à refacturer
    :param uuid_identification: uuid_identification de la trace
    :return:
    """
    sql_kwargs = get_sql_kwargs(supplier_origin, period_rfa, uuid_identification)

    with connection.cursor() as cursor:
        cursor.execute(SQL_INSERTION_ICON)
        cursor.execute(SQL_RFA_INSERTION, sql_kwargs)
        return cursor.rowcount
