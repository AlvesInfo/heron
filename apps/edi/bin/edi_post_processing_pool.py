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
    "qty" = case 
                when "qty" = 0 or qty isnull 
                then 1::numeric 
                else "qty" 
            end,
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
    sql_supplier_update = sql.SQL(
        """
        update "edi_ediimport" "edi"
        set 
            "supplier_name" = "tiers"."name",
            "third_party_num" = "tiers"."third_party_num",
            "supplier" = case 
                            when "supplier" = '' or "supplier" isnull 
                            then "tiers"."name" 
                            else "supplier" 
                         end
        from (
            select 
                left("name", 35) as "name",
                "third_party_num",
                unnest(string_to_array("centers_suppliers_indentifier", '|')) as "identifier"
                from "book_society" bs
        ) "tiers"
        where ("edi"."third_party_num" is null or "edi"."third_party_num" = '')
        and "edi"."supplier_ident" = "tiers"."identifier"
        and ("edi"."valid" = false or "edi"."valid" isnull)
        """
    )
    sql_fac_update_except_edi = sql.SQL(
        """
    update "edi_ediimport" edi
    set
        "invoice_amount_without_tax" = edi_fac."invoice_amount_without_tax",
        "invoice_amount_with_tax" = edi_fac."invoice_amount_with_tax",
        "invoice_amount_tax" = (
                                    edi_fac."invoice_amount_with_tax" 
                                    - 
                                    edi_fac."invoice_amount_without_tax"
                                ),
        "reference_article" = case 
                                when "reference_article" isnull or "reference_article" = '' 
                                then "ean_code"
                                else "reference_article"
                              end
    from (
        select
            "uuid_identification",
            "invoice_number",
            case 
                when invoice_type = '381' 
                then -abs(sum("mont_HT"))::numeric
                else abs(sum("mont_HT"))::numeric
            end as "invoice_amount_without_tax",
            case 
                when invoice_type = '381'
                then -abs(sum("mont_TTC"))::numeric 
                else abs(sum("mont_TTC"))::numeric    
            end as "invoice_amount_with_tax"
        from (
            select
                "uuid_identification",
                "invoice_number",
                "invoice_type",
                round(sum("net_amount")::numeric, 2) as "mont_HT",
                (
                    round(sum("net_amount")::numeric, 2) +
                    round(round(sum("net_amount")::numeric, 2) * "vat_rate"::numeric, 2)
                ) as "mont_TTC",
                "vat_rate"
            from "edi_ediimport"                
            where (flow_name != 'Edi')
            and ("valid" = false or "valid" isnull)
            group by "uuid_identification", "invoice_number", "vat_rate", "invoice_type"
        ) as "tot_amount"
        group by "uuid_identification", "invoice_number", "invoice_type"
    ) edi_fac
    where edi."uuid_identification" = edi_fac."uuid_identification"
    and edi."invoice_number" = edi_fac."invoice_number"
    """
    )
    sql_reference = """
    update edi_ediimport 
    set
        reference_article = libelle 
    where (reference_article isnull or reference_article = '')
      and ("valid" = false or "valid" isnull)
    """
    sql_validate = sql.SQL(
        """
        update "edi_ediimport" edi
        set
            "valid"=true,
            "vat_rate_exists" = false,
            "supplier_exists" = false,
            "maison_exists" = false,
            "article_exists" = false,
            "axe_pro_supplier_exists" = false,
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
    """
    )
    with connection.cursor() as cursor:
        cursor.execute(sql_supplier_update)
        cursor.execute(sql_fac_update_except_edi)
        cursor.execute(sql_reference)
        cursor.execute(sql_validate)


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
                "flow_name",
                "supplier",
                "supplier_ident",
                "code_fournisseur",
                "acuitis_order_number",
                "delivery_number",
                "invoice_number",
                "invoice_date",
                "invoice_type",
                "devise",
                "vat_rate",
                "invoice_amount_without_tax",
                "invoice_amount_tax",
                "invoice_amount_with_tax",
                "uuid_identification",
                "packaging_amount",
                "transport_amount",
                "insurance_amount",
                "fob_amount",
                "fees_amount",
                "command_reference",
            )
            .first()
        )

        for key, value in packaging_dict.items():
            if key in charges_dict and value:
                libelle = charges_dict.get(key)

                bulk_list.append(
                    EdiImport(
                        uuid_identification=edi.get("uuid_identification"),
                        flow_name=edi.get("flow_name"),
                        supplier=edi.get("supplier"),
                        supplier_ident=edi.get("supplier_ident"),
                        code_fournisseur=edi.get("code_fournisseur"),
                        acuitis_order_number=edi.get("acuitis_order_number"),
                        delivery_number=edi.get("delivery_number"),
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
                        invoice_amount_without_tax=edi.get("invoice_amount_without_tax"),
                        invoice_amount_tax=edi.get("invoice_amount_tax"),
                        invoice_amount_with_tax=edi.get("invoice_amount_with_tax"),
                        command_reference=edi.get("command_reference"),
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

    sql_col_essilor = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "supplier_ident" = 'col_opticlibre'
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    and "siret_payeur" in ('9524514', '433193067', '43319306700033', 'FR82433193067')
    """
    )
    sql_tva = sql.SQL(
        """
    update edi_ediimport
    set
        vat_rate =  case
                        when vat_rate = 5.5 then 0.055
                        when vat_rate = 20 then 0.20
                        else vat_rate
                    end,
        acuitis_order_number = case 
                                    when acuitis_order_number = 'UNKNOWN' 
                                    then '' 
                                    else acuitis_order_number
                                end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_fac_update_edi = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "net_amount" = case
                            when ("invoice_type" = '381' and "qty" < 0) 
                              or ("invoice_type" = '380' and "qty" > 0) 
                            then abs("net_amount")::numeric
                            when ("invoice_type" = '381' and "qty" > 0) 
                              or ("invoice_type" = '380' and "qty" < 0) 
                            then -abs("net_amount")::numeric
                        end,
        "invoice_amount_without_tax" = case 
                                when invoice_type = '381' 
                                then -abs("invoice_amount_without_tax")::numeric
                                else abs("invoice_amount_without_tax")::numeric
                              end,
        "invoice_amount_with_tax" = case 
                                        when invoice_type = '381'
                                        then -abs("invoice_amount_with_tax")::numeric
                                        else abs("invoice_amount_with_tax")::numeric  
                                      end,
        "invoice_amount_tax" = case 
                                when invoice_type = '381'
                                then -abs("invoice_amount_with_tax")::numeric
                                else abs("invoice_amount_with_tax")::numeric
                              end -
                              case 
                                when invoice_type = '381' 
                                then -abs("invoice_amount_without_tax")::numeric
                                else abs("invoice_amount_without_tax")::numeric
                              end,
        "reference_article" = case 
                                when "reference_article" isnull or "reference_article" = '' 
                                then "ean_code"
                                else "reference_article"
                              end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_col_essilor, {"uuid_identification": uuid_identification})
        cursor.execute(sql_tva, {"uuid_identification": uuid_identification})
        cursor.execute(sql_fac_update_edi, {"uuid_identification": uuid_identification})


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
    sql_update_units = sql.SQL(
        """
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
    )

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
    sql_net_amount_mgdev = sql.SQL(
        """
    update "edi_ediimport" edi
    set
        "net_amount" = case
                            when ("invoice_type" = '381' and "qty" < 0) 
                              or ("invoice_type" = '380' and "qty" > 0) 
                            then abs("net_amount")::numeric
                            when ("invoice_type" = '381' and "qty" > 0) 
                              or ("invoice_type" = '380' and "qty" < 0) 
                            then -abs("net_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount_mgdev, {"uuid_identification": uuid_identification})


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
        "net_amount" = round("net_unit_price"::numeric * "qty"::numeric, 2)::numeric,
        "reference_article" = case 
                                when "reference_article" = '' or "reference_article" is null 
                                then left("libelle", 35)
                                else "reference_article"
                              end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_bl_date = sql.SQL(
        """
        update "edi_ediimport" "edi" 
        set
            "delivery_number" = "sd"."single_delivery_number",
            "delivery_date" = "sd"."single_date"::date
        from (
            select
                "id",
                case 
                    when "delivery_number" ilike '%% du %%'  
                        and is_date(split_part("delivery_number", ' du ', 2))
                    then split_part(delivery_number, ' du ', 1) 
                else "delivery_number"
                end as "single_delivery_number",
                case 
                    when "delivery_number" ilike '%% du %%' 
                        and is_date(split_part("delivery_number", ' du ', 2))
                    then TO_DATE(split_part("delivery_number", ' du ', 2),'DD/MM/YYYY')::varchar
                    else null 
                end as "single_date"
                
            from "edi_ediimport" r
            where 
                case 
                    when "delivery_number" ilike '%% du %%' 
                        and is_date(split_part("delivery_number", ' du ', 2))
                    then TO_DATE(split_part("delivery_number", ' du ', 2),'DD/MM/YYYY')::varchar
                    else null 
                end is not null
            and "uuid_identification" = %(uuid_identification)s
            and ("valid" = false or "valid" isnull)
        ) "sd"
        where "edi"."id" = "sd"."id"
        """
    )
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_bl_date, {"uuid_identification": uuid_identification})


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

    sql_update_vat_rate = sql.SQL(
        """
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
    )

    sql_update_units = sql.SQL(
        """
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
    )

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
        "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
        "famille" = left("reference_article", 2)
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_round_net_amount = sql.SQL(
        """
    update "edi_ediimport"
    set 
        "net_amount" = round("net_amount", 2)::numeric,
        "amount_with_vat" = round(round("amount_with_vat", 2) * (1 + "vat_rate"), 2)::numeric
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    sql_net_amount = sql.SQL(
        """
    update "edi_ediimport" edi
    set
        "net_amount" = case
                            when ("invoice_type" = '381' and "qty" < 0) 
                              or ("invoice_type" = '380' and "qty" > 0) 
                            then abs("net_amount")::numeric
                            when ("invoice_type" = '381' and "qty" > 0) 
                              or ("invoice_type" = '380' and "qty" < 0) 
                            then -abs("net_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_round_net_amount, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount, {"uuid_identification": uuid_identification})


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
    sql_net_amount = sql.SQL(
        """
    update "edi_ediimport" edi
    set
        "net_amount" = case
                            when ("invoice_type" = '381' and "qty" < 0) 
                              or ("invoice_type" = '380' and "qty" < 0) 
                            then -abs("net_amount")::numeric
                            when ("invoice_type" = '381' and "qty" > 0) 
                              or ("invoice_type" = '380' and "qty" > 0) 
                            then abs("net_amount")::numeric
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount, {"uuid_identification": uuid_identification})


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
                            when "invoice_type" = '400' then '381' 
                            -- 400 = RFA
                            else '380' 
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
                        end,
        "famille" = case
                        when "libelle" ilike 'DELIVERY%%' then 'PORT'
                        when "libelle" ilike '%%FREIGHT%%' then 'PORT'
                        when "libelle" ilike 'WARRANTY%%' then 'WARRANTY'
                        when "libelle" ilike 'DISCOUNT INSTANT' then 'RFA'
                        else "famille"
                    end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    sql_update_bl = """
    update "edi_ediimport" "ei"
    set "delivery_number" = "req"."delivery_number"
    from (
        select 
            max("delivery_number") as "delivery_number", 
            "invoice_number", 
            "uuid_identification"
        from "edi_ediimport"
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        group by "invoice_number", "uuid_identification"
        HAVING 
            max("delivery_number") != '' 
        and max("delivery_number") is not null
    ) "req" 
    where 
        "ei"."invoice_number" = "req"."invoice_number"
    and	"ei"."uuid_identification"= "req"."uuid_identification"
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_bl, {"uuid_identification": uuid_identification})


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
    with "group_technidis" as (
        select 
            case when sum(net_amount) < 0 then '381' else '380' end as "invoice_type", 
            "invoice_number", 
            "uuid_identification"
          from "edi_ediimport" 
         where "uuid_identification" = %(uuid_identification)s
           and ("valid" = false or "valid" isnull)
         group by "invoice_number", "uuid_identification"
    )
    update "edi_ediimport" "ei"
       set "invoice_type" = "gt"."invoice_type"
      from "group_technidis" "gt"
     where "ei"."uuid_identification" = "gt"."uuid_identification"
       and "ei"."invoice_number" = "gt"."invoice_number"
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
                        end,
        "famille" =   case 
                                    when "famille" is null or "famille" = ''
                                    then split_part("reference_article", '-', 1)
                                    else "famille"
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

    sql_update_units = sql.SQL(
        """
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
    )

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

    sql_update_units = sql.SQL(
        """
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
    )

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
