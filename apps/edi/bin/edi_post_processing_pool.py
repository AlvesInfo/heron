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

from psycopg2 import sql
from django.db import connection
from django.db.models import Q, Count

from apps.edi.models import EdiImport

SQL_QTY = sql.SQL(
    """
update "edi_ediimport"
set 
    "qty" = case when "qty" = 0 or qty isnull then 1::numeric else "qty" end,
    "devise" = case when "devise" is null then 'EUR' else "devise" end,
    "active" = false,
    "to_delete" = false,
    "to_export" = false
where ("valid" = false or "valid" isnull)
and uuid_identification = %(uuid_identification)s
"""
)


def post_processing_all():
    """Mise à jour de l'ensemble des factures après tous les imports et parsing"""
    sql_fac_update = sql.SQL(
        """
    update "edi_ediimport" edi
    set
        "montant_facture_HT" = edi_fac."montant_facture_HT",
        "montant_facture_TVA" = edi_fac."montant_facture_TVA",
        "montant_facture_TTC" = edi_fac."montant_facture_TTC",
        "valid"=true
    from (
        select
            "uuid_identification",
            "invoice_number",
            sum("mont_HT") as "montant_facture_HT",
            sum("mont_TVA") as "montant_facture_TVA",
            sum("mont_TTC") as "montant_facture_TTC"
        from (
            select
                "uuid_identification",
                "invoice_number",
                sum("montant_HT")::numeric as "mont_HT",
                round((sum("montant_HT")::numeric * "vat_rate"::numeric), 2) as "mont_TVA",
                (
                    sum("montant_HT")::numeric +
                    round((sum("montant_HT")::numeric * "vat_rate"::numeric), 2)
    
                ) as "mont_TTC",
                "vat_rate"
            from (
                select
                    "uuid_identification",
                    "invoice_number",
                    round(sum("net_amount")::numeric, 2) as "montant_HT",
                    "vat_rate"
                from "edi_ediimport"
                where ("valid" = false or "valid" isnull)
                and (
                    ("montant_facture_TTC" isnull or "montant_facture_TTC" = 0)
                    or 
                    ("montant_facture_HT" isnull or "montant_facture_HT" = 0)
                )
                group by "uuid_identification", "invoice_number", "vat_rate"
            ) as vat_tot
            group by "uuid_identification", "invoice_number", "vat_rate"
        ) as "tot_amount"
        group by "uuid_identification", "invoice_number"
    ) edi_fac
    where edi."uuid_identification" = edi_fac."uuid_identification"
    and edi."invoice_number" = edi_fac."invoice_number"
    """
    )
    with connection.cursor() as cursor:
        cursor.execute(sql_fac_update)


def bulk_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Bulk
    et rajout des lignes de port et d'emballage en EMB et PORT en créant des lignes
    :param uuid_identification: uuid_identification
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
        .filter(uuid_identification=uuid_identification)
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
                "uuid_identification",
                "packaging_amount",
                "transport_amount",
                "insurance_amount",
                "fob_amount",
                "fees_amount",
            )
            .first()
        )

        for key, value in packaging_dict.items():
            if key in charges_dict and value:
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
                        vat_rate=edi.get("vat_rate"),
                        montant_facture_HT=edi.get("montant_facture_HT"),
                        montant_facture_TVA=edi.get("montant_facture_TVA"),
                        montant_facture_TTC=edi.get("montant_facture_TTC"),
                    )
                )

    if bulk_list:
        EdiImport.objects.bulk_create(bulk_list)

    # Mise à jour des autres champs ================================================================
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "famille" = case when "famille" is null then 'VERRE' else "famille" end,
        "gross_unit_price" = "net_unit_price",
        "gross_amount" = "net_amount"
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        EdiImport.objects.filter(uuid_identification=uuid_identification).update(valid=True)


def edi_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Opto33 EDI
    :param uuid_identification: uuid_identification
    """
    sql_update_fac_tva = """
    update "edi_ediimport"
    set 
        "montant_facture_TVA" = "montant_facture_TTC" - "montant_facture_HT",
        "reference_article" = case 
                                when "reference_article" isnull or "reference_article" = '' 
                                then "ean_code"
                                else "reference_article"
                              end,
        "acuitis_order_date" = case 
                                when "acuitis_order_date" = '1900-01-01' 
                                then null
                                else "acuitis_order_date"
                               end,
        "delivery_date" = case 
                            when "delivery_date" = '1900-01-01' 
                            then null
                            else "delivery_date"
                           end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    sql_valid = """
    update "edi_ediimport"
    set 
        "valid"=true
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_fac_tva, {"uuid_identification": uuid_identification})
        cursor.execute(sql_valid, {"uuid_identification": uuid_identification})


def eye_confort_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "vat_rate" = 0,
        "vat_amount" = 0,
        "amount_with_vat" = "net_amount"::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 then (abs("gross_amount")::numeric * -1::numeric)
                            when "net_amount" > 0 then abs("gross_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})


def generique_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def hearing_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Hearing
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "net_amount" = round("net_amount"::numeric, 2)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def interson_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Interson
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_amount" = ("gross_unit_price"::numeric * "qty"::numeric)::numeric,
        "net_amount" = round("net_unit_price"::numeric * "qty"::numeric, 2)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def johnson_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier JOHNSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "qty" >= 0 then '380' else '381' end,
        "gross_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "gross_amount" = "net_amount"::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_vat_rate = """
    update "edi_ediimport" "ed" 
    set "vat_rate" = "req"."taux_tva" 
    from (
        select
            case 
                when "net_amount" isnull or "net_amount" = 0 then 0
                when round("amount_with_vat"::numeric/"net_amount"::numeric, 2) 
                        between 1.19 and 1.21 
                        then .2 
                when round("amount_with_vat"::numeric/"net_amount"::numeric, 2) 
                        between 1.045 and 1.065 
                        then .055
            end as "taux_tva",
            "uuid_identification", 
            "edi"."id"
        from "edi_ediimport" "edi"
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
    ) "req" 
    where "req"."id" = "ed"."id"
    """
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 then (abs("gross_amount")::numeric * -1::numeric)
                            when "net_amount" > 0 then abs("gross_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_vat_rate, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})


def lmc_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier LMC
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_amount" = ("gross_unit_price"::numeric * "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def newson_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def phonak_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def prodition_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
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
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    sql_update = sql.SQL(
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
        "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s 
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_libele, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def signia_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier SIGNA
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
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
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 then (abs("gross_amount")::numeric * -1::numeric)
                            when "net_amount" > 0 then abs("gross_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})


def starkey_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 
                                then (
                                    abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                    * 
                                    -1::numeric
                                )
                            when "net_amount" > 0 
                                then (
                                    abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                )
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})


def technidis_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'F' then '380' else '381' end,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 
                                then (
                                    abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                    * 
                                    -1::numeric
                                )
                            when "net_amount" > 0 
                                then (
                                    abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                )
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})


def unitron_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})


def widex_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "famille" = case 
                        when "famille" = '' or "famille" is null 
                        then "reference_article" 
                        else "famille" 
                    end,
        "gross_amount" = case 
                            when "gross_amount" is null or "gross_amount" = 0 
                            then "net_amount"::numeric 
                            else "gross_amount"::numeric 
                        end,
        "gross_unit_price" = (
            case 
                when "gross_amount" is null or "gross_amount" = 0 
                then "net_amount"::numeric 
                else "gross_amount"::numeric 
            end 
            / "qty"::numeric
        )::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 then (abs("gross_amount")::numeric * -1::numeric)
                            when "net_amount" > 0 then abs("gross_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})


def widexga_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
        "famille" = case 
                        when "famille" = '' or "famille" is null 
                        then "reference_article" 
                        else "famille" 
                    end,
        "gross_amount" = case 
                            when "gross_amount" is null or "gross_amount" = 0 
                            then "net_amount"::numeric 
                            else "gross_amount"::numeric 
                        end,
        "gross_unit_price" = (
            case 
                when "gross_amount" is null or "gross_amount" = 0 
                then "net_amount"::numeric 
                else "gross_amount"::numeric 
            end 
            / "qty"::numeric
        )::numeric,
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_update_units = """
    update "edi_ediimport"
    set 
        "qty" = case 
                    when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                    when "net_amount" > 0 then abs("qty")::numeric
                    else "qty" 
                end,
        "gross_unit_price" = abs("gross_unit_price"),
        "net_unit_price" = abs("net_unit_price"),
        "gross_amount" = case 
                            when "net_amount" = 0 then 0
                            when "net_amount" < 0 then (abs("gross_amount")::numeric * -1::numeric)
                            when "net_amount" > 0 then abs("gross_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
