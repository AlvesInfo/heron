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

from psycopg2 import sql
from django.db import connection, transaction
from django.db.models import Q

from apps.book.models import Society
from apps.edi.models import EdiValidation
from apps.core.functions.functions_dates import last_day_month


@transaction.atomic
def insert_rfa(supplier_origin: AnyStr, period_rfa: AnyStr, uuid_identification: UUID):
    """Génération des RFA
    :param supplier_origin: Fournisseur dont il faut générer les RFA
    :param period_rfa: Période de RFA à refacturer
    :param uuid_identification: uuid_identification de la trace
    :return:
    """
    period = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()
    last_day = last_day_month(period.billing_period)
    invoice_number = (
        f"{supplier_origin}_"
        f"{str(last_day.month).zfill(2)}_"
        f"{str(last_day.year)}_"
        "001"
    )
    invoice_date = last_day.isoformat()
    reference_article = period_rfa
    society = Society.objects.get(third_party_num=supplier_origin)
    zcaha = Society.objects.get(third_party_num="ZCAHA")
    third_party_num = zcaha.third_party_num
    supplier = f"{zcaha.short_name} RFA"
    supplier_name = zcaha.short_name
    supplier_ident = str(zcaha.centers_suppliers_indentifier).split("|")[0]
    libelle = (
        f"{society.short_name} "
        "RFA "
        f"{str(last_day.month).zfill(2)}/"
        f"{str(last_day.year)}"
    )
    familly = "AA"
    vat_rate = "550"
    vat = "002"
    print("uuid_identification : ", uuid_identification)
    print("third_party_num : ", third_party_num)
    print("supplier_ident : ", supplier_ident)
    print("supplier : ", supplier)
    print("siret_payeur : ", supplier)
    print("invoice_number : ", invoice_number)
    print("invoice_date : ", invoice_date)
    print("reference_article : ", reference_article)
    print("libelle : ", libelle)
    print("supplier_name : ", supplier_name)
    print("familly : ", familly)
    print("vat_rate : ", vat_rate)
    print("vat : ", vat)


if __name__ == '__main__':
    insert_rfa("WIDE001", "2024RFA_07", uuid4())
