# pylint: disable=E0401,C0303,E1101,R0915,R0914
"""
FR : Module des génération des RFA
EN : RFA Generation Module

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""

from typing import AnyStr
from uuid import UUID, uuid4

from django.db import connection, transaction
from django.db.models import Q

from apps.book.models import Society
from apps.edi.models import EdiValidation
from apps.core.functions.functions_dates import last_day_month
from apps.rfa.sql_files.sql_rfa import SQL_RFA_INSERTION


def get_sql_kwars(
    supplier_origin: AnyStr, period_rfa: AnyStr, uuid_identification: UUID
):
    """Retourne le dictionnaire des arguments de la requête
    :param supplier_origin: Fournisseur dont il faut générer les RFA
    :param period_rfa: Période de RFA à refacturer
    :param uuid_identification: uuid_identification de la trace
    :return:
    """
    period = EdiValidation.objects.filter(
        Q(final=False) | Q(final__isnull=True)
    ).first()
    last_day = last_day_month(period.billing_period)
    society = Society.objects.get(third_party_num=supplier_origin)

    sql_kwargs = {
        "uuid_identification": uuid_identification,
        "third_party_num": society.third_party_num,
        "supplier": f"{society.short_name} RFA",
        "supplier_ident": str(society.centers_suppliers_indentifier).split(
            "|", maxsplit=1
        )[0],
        "supplier_name": society.short_name,
        "siret_payeur": f"{society.short_name} RFA",
        "invoice_number": (
            f"{supplier_origin}_"
            f"{str(last_day.month).zfill(2)}_"
            f"{str(last_day.year)}_"
        ),
        "invoice_date": last_day.isoformat(),
        "reference_article": period_rfa,
        "libelle": (
            "RFA "
            f"{society.short_name} "
            f"{str(last_day.month).zfill(2)}/"
            f"{str(last_day.year)}"
        ),
        "familly": "AA",
        "vat_rate": "550",
        "vat": "002",
        "flow_name": "rfa_flow",
    }
    return sql_kwargs


@transaction.atomic
def insert_rfa(supplier_origin: AnyStr, period_rfa: AnyStr, uuid_identification: UUID):
    """Génération des RFA
    :param supplier_origin: Fournisseur dont il faut générer les RFA
    :param period_rfa: Période de RFA à refacturer
    :param uuid_identification: uuid_identification de la trace
    :return:
    """
    sql_kwargs = get_sql_kwars(supplier_origin, period_rfa, uuid_identification)

    with connection.cursor() as cursor:
        query = SQL_RFA_INSERTION
        # print(cursor.mogrify(query, sql_kwargs).decode())
        cursor.execute(query, sql_kwargs)
        return cursor.rowcount


if __name__ == "__main__":
    insert_rfa("WIDE001", "2024RFA_07", uuid4())
