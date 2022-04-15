# pylint: disable=E0401,C0303
"""
FR : Module de post-traitement avant import des fichiers de factures fournisseur
EN : Post-processing module before importing supplier invoice files

Commentaire:

created at: 2022-04-10
created by: Paulo ALVES

modified at: 2022-04-10
modified by: Paulo ALVES
"""
from typing import AnyStr
from decimal import Decimal

from psycopg2 import sql
from django.db import connection
from django.db.models import Q, Count

from apps.edi.models import EdiImport

sql_qty = sql.SQL(
    """
update "edi_ediimport"
set 
    "qty" = case when "qty" = 0 or qty isnull then 1::numeric else "qty" end,
    "devise" = case when "devise" is null then 'EUR' else "devise" end,
    "active" = false,
    "to_delete" = false,
    "to_export" = false
where ("valid" = false or "valid" isnull)
"""
)
taux_tva_par_defaut = Decimal("0.2")


def bulk_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Bulk
    et rajout des lignes de port et d'emballage en EMB et PORT en créant des lignes
    :param flow_name: flow_name
    """
    charges_dict = {
        "packaging_amount": "EMBALLAGE",
        "transport_amount": "PORT",
        "insurance_amount": "INSURANCE",
        "fob_amount": "FOB",
        "fees_amount": "FEES",
    }

    # Ajout des lignes de packaging pour la facture concernée ======================================
    packaging_amount_dict = (
        EdiImport.objects.filter(Q(valid=False) | Q(valid__isnull=True))
        .exclude(Q(packaging_amount=0) | Q(packaging_amount__isnull=True))
        .filter(flow_name=flow_name)
        .values("invoice_number", *list(charges_dict))
        .annotate(dcount=Count("invoice_number"))
    )
    bulk_list = []

    for packaging_dict in packaging_amount_dict:
        edi = (
            EdiImport.objects.filter(invoice_number=packaging_dict.get("invoice_number"))
            .values(
                "uuid_identification",
                "supplier",
                "supplier_ident",
                "code_fournisseur",
                "invoice_number",
                "invoice_date",
                "invoice_type",
                "devise",
                "vat_rate",
                "montant_facture_HT",
                "montant_facture_TVA",
                "montant_facture_TTC",
            )
            .first()
        )
        vat_rate = edi.get("vat_rate")

        for key, value in packaging_dict.items():
            if key in charges_dict and value:
                print(edi.get("invoice_number"), edi.get("montant_facture_TTC"))
                libelle = charges_dict.get(key)
                bulk_list.append(
                    EdiImport(
                        uuid_identification=edi.get("uuid_identification"),
                        supplier=edi.get("supplier"),
                        supplier_ident=edi.get("supplier_ident"),
                        code_fournisseur=edi.get("code_fournisseur"),
                        invoice_number=edi.get("invoice_number"),
                        invoice_date=edi.get("invoice_date"),
                        invoice_type=edi.get("invoice_type"),
                        devise=edi.get("devise"),
                        reference_article=libelle,
                        libelle=libelle,
                        famille=libelle,
                        net_unit_price=value,
                        net_amount=value,
                        vat_rate=vat_rate,
                        montant_facture_HT=edi.get("montant_facture_HT"),
                        montant_facture_TVA=edi.get("montant_facture_TVA"),
                        montant_facture_TTC=edi.get("montant_facture_TTC"),
                    )
                )
                print(edi.get("montant_facture_TTC"))
    EdiImport.objects.bulk_create(bulk_list)

    # Mise à jour des autres champs ================================================================
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "famille" = case when "famille" is null then 'VERRE' else "famille" end,
        "gross_unit_price" = "net_unit_price",
        "gross_price" = "net_amount"
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_update)

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def eye_confort_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_price"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def generique_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def hearing_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Hearing
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_price"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def interson_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Interson
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_price" = ("gross_unit_price"::numeric * "qty"::numeric)::numeric,
        "net_amount" = round("net_unit_price"::numeric * "qty"::numeric, 2)::numeric,
        "vat_amount" = (
            "amount_with_vat"::numeric 
            - 
            round("net_unit_price"::numeric * "qty"::numeric, 2)::numeric
        )::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def johnson_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier JOHNSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "qty" >= 0 then '380' else '381' end,
        "gross_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "gross_price" = "net_amount"::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def lmc_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier LMC
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_price" = ("gross_unit_price"::numeric * "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def newson_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_price"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def phonak_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_price"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def prodition_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_libele = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "qty" = case when "qty" = 0 then 1::numeric else "qty" end,
        "libelle"= case 
                        when "libelle" is null or "libelle" = ''
                        then "famille" 
                        else "libelle" 
                    end
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "reference_article"= case 
                                when "reference_article" is null or "reference_article" = ''
                                then "famille" 
                                else "reference_article" 
                            end,
        "libelle"= case 
                        when "libelle" is null or "libelle" = ''
                        then "reference_article" 
                        else "libelle" 
                    end,
        "gross_unit_price" = ("gross_price"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_libele)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def signia_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier SIGNA
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "qty" = case when "qty" = 0 then 1::numeric else "qty" end,
        "invoice_type" = case 
                            when "invoice_type" = '301' then '380' 
                            when "invoice_type" = '307' then '380' 
                            when "invoice_type" = '302' then '381' 
                            when "invoice_type" = '304' then '381' 
                            else '400' 
                        end
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def starkey_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def technidis_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'F' then '380' else '381' end,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def unitron_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_price"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def widex_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "famille" = case 
                        when "famille" = '' or "famille" is null 
                        then "reference_article" 
                        else "famille" 
                    end,
        "gross_price" = case 
                            when "gross_price" is null or "gross_price" = 0 
                            then "net_amount"::numeric 
                            else "gross_price"::numeric 
                        end,
        "gross_unit_price" = (
            case 
                when "gross_price" is null or "gross_price" = 0 
                then "net_amount"::numeric 
                else "gross_price"::numeric 
            end 
            / "qty"::numeric
        )::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)


def widexga_post_insert(flow_name: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param flow_name: flow_name
    """
    sql_base_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "famille" = case 
                        when "famille" = '' or "famille" is null 
                        then "reference_article" 
                        else "famille" 
                    end,
        "gross_price" = case 
                            when "gross_price" is null or "gross_price" = 0 
                            then "net_amount"::numeric 
                            else "gross_price"::numeric 
                        end,
        "gross_unit_price" = (
            case 
                when "gross_price" is null or "gross_price" = 0 
                then "net_amount"::numeric 
                else "gross_price"::numeric 
            end 
            / "qty"::numeric
        )::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_amount" = ("amount_with_vat"::numeric - "net_amount"::numeric)::numeric
    where "flow_name" = '{flow_name}' 
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set 
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC"    
    from (
        select 
            "invoice_number",
            sum("net_amount") as "montant_facture_HT",
            sum("vat_amount") as "montant_facture_TVA",
            sum("amount_with_vat") as "montant_facture_TTC"
        from "edi_ediimport" 
        where "flow_name" = '{flow_name}'
        group by "invoice_number"
    ) edi_fac
    where edi."flow_name" = '{flow_name}' 
    and edi."invoice_number" = edi_fac."invoice_number"
    and ("valid" = false or "valid" isnull)
    """
    ).format(flow_name=sql.SQL(flow_name))

    with connection.cursor() as cursor:
        cursor.execute(sql_qty)
        cursor.execute(sql_base_update)
        cursor.execute(sql_fac_update)
        EdiImport.objects.filter(flow_name=flow_name).update(valid=True)
