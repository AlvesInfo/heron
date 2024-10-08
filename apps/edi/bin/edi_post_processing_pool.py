# pylint: disable=E0401,C0303,E1101,R0915,R0914
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

from django.db import connection
from django.db.models import Q, Count

from apps.edi.models import EdiImport
from apps.data_flux.models import Trace
from apps.edi.bin.duplicates_check import (
    edi_import_duplicate_check,
    suppliers_invoices_duplicate_check,
)
from apps.edi.bin.edi_articles_news import set_axes_with_regex
from apps.edi.bin.set_suppliers_cct import add_news_cct_sage, set_signboard
from apps.edi.sql_files.sql_common import post_common_dict
from apps.edi.sql_files.sql_all import post_all_dict, SQL_QTY
from apps.edi.sql_files.sql_bulk import post_bulk_dict
from apps.edi.sql_files.sql_bbgr_002_statment import bbgr_002_statment_dict
from apps.edi.sql_files.sql_bbgr_003_monthly import bbgr_003_monthly_dict
from apps.edi.sql_files.sql_bbgr_004_retours import bbgr_004_retours_dict
from apps.edi.sql_files.sql_bbgr_005_receptions import bbgr_005_receptions_dict
from apps.edi.sql_files.sql_cosium import post_cosium_dict
from apps.edi.sql_files.sql_cosium_achat import post_cosium_achats_dict
from apps.edi.sql_files.sql_transferts_cosium import post_transfert_cosium_dict
from apps.edi.sql_files.sql_edi import post_edi_dict
from apps.edi.sql_files.sql_eye_confort import post_eye_dict
from apps.edi.sql_files.sql_generic import post_generic_dict, post_generic_internal_dict
from apps.edi.sql_files.sql_hearing import post_hearing_dict
from apps.edi.sql_files.sql_interson import post_interson_dict
from apps.edi.sql_files.sql_johnson import post_johnson_dict
from apps.edi.sql_files.sql_lmc import post_lmc_dict
from apps.edi.sql_files.sql_newson import post_newson_dict
from apps.edi.sql_files.sql_phonak import post_phonak_dict
from apps.edi.sql_files.sql_prodition import post_prodition_dict
from apps.edi.sql_files.sql_signia import post_signia_dict
from apps.edi.sql_files.sql_starkey import post_starkey_dict
from apps.edi.sql_files.sql_technidis import post_technidis_dict
from apps.edi.sql_files.sql_unitron import post_unitron_dict
from apps.edi.sql_files.sql_widex import post_widex_dict
from apps.edi.sql_files.sql_z_bu_refac import post_z_bu_refac

from apps.users.models import User


def get_user_automate():
    """Recuperation de l'uuid de l'automate"""
    email = "automate@acuitis.com"
    user, _ = User.objects.get_or_create(
        username="automate",
        email=email,
        password=email,
        first_name="automate",
        last_name="automate",
        function="automate",
    )

    return user.uuid_identification


def suppress_import_without_articles():
    """Vérification qu'il n'y ait pas de lignes d'import sans artilces,
    sinon on les rejette et on met la trace en erreur
    """
    without_reference_list = (
        EdiImport.objects.filter(Q(reference_article__isnull=True) | Q(reference_article=""))
        .values("uuid_identification")
        .annotate(dcount=Count("uuid_identification"))
        .values("uuid_identification")
        .order_by()
        .values_list("uuid_identification", flat=True)
    )

    for uuid_identification in without_reference_list:
        try:
            trace = Trace.objects.get(uuid_identification=uuid_identification)
            trace.errors = True
            trace.comment = (
                "Une erreur c'est produite."
                "<br>Il manque des références articles dans le fichier."
                "<br>Le fichier a été réjeté!"
            )
            trace.save()
            EdiImport.objects.filter(uuid_identification=uuid_identification).delete()

        except Trace.DoesNotExist:
            pass


def post_processing_all():
    """Mise à jour de l'ensemble des factures après tous les imports et parsing"""
    # suppression des imports sans articles
    suppress_import_without_articles()

    # Mise à jour sur la fiche tiers, du champ courant, pour l'affichage plus rapide des tiers
    sql_in_use_third_party_num = post_all_dict.get("sql_in_use_third_party_num")
    sql_update_item_weight = post_all_dict.get("sql_update_item_weight")
    sql_orpheans = post_all_dict.get("sql_orpheans")

    with connection.cursor() as cursor:
        cursor.execute(sql_in_use_third_party_num)
        cursor.execute(sql_update_item_weight)
        cursor.execute(sql_orpheans)

    edi_import_duplicate_check()
    suppliers_invoices_duplicate_check()
    add_news_cct_sage()
    set_signboard()
    set_axes_with_regex()

    sql_update_bu = post_all_dict.get("sql_update_bu")
    sql_update_bu_articles = post_all_dict.get("sql_update_bu_articles")

    with connection.cursor() as cursor:
        cursor.execute(sql_update_bu)
        cursor.execute(sql_update_bu_articles)


def post_vacuum():
    """Mise à jour de l'ensemble des factures après tous les imports et parsing"""
    with connection.cursor() as cursor:
        cursor.execute("VACUUM (full)")


def post_general(uuid_identification: AnyStr, cursor: connection.cursor):
    """Mise à jour générale pour tous les founrnisseurs"""
    sql_round_amount = post_common_dict.get("sql_round_amount")
    sql_supplier_update = post_common_dict.get("sql_supplier_update")
    sql_supplier_name_update = post_common_dict.get("sql_supplier_name_update")
    sql_fac_update_except_edi = post_common_dict.get("sql_fac_update_except_edi")
    sql_reference = post_common_dict.get("sql_reference")
    sql_cct = post_common_dict.get("sql_cct")
    sql_is_multi_store_true = post_common_dict.get("sql_is_multi_store_true")
    sql_is_multi_store_false = post_common_dict.get("sql_is_multi_store_false")
    sql_update_articles = post_common_dict.get("sql_update_articles")
    sql_alls_381 = post_common_dict.get("sql_alls_381")
    sql_vat_regime = post_common_dict.get("sql_vat_regime")
    sql_vat = post_common_dict.get("sql_vat")
    vat_per_line = post_common_dict.get("vat_per_line")
    sql_delta_vat = post_common_dict.get("sql_delta_vat")
    sql_none = post_common_dict.get("sql_none")
    sql_delivery_number = post_common_dict.get("sql_delivery_number")
    sql_signboard = post_common_dict.get("sql_signboard")
    sql_center = post_common_dict.get("sql_center")
    sql_import_uuid_identification = post_common_dict.get("sql_import_uuid_identification")
    sql_purchase_vat_cee = post_common_dict.get("sql_purchase_vat_cee")
    sql_validate = post_common_dict.get("sql_validate")

    cursor.execute(sql_round_amount, {"uuid_identification": uuid_identification})
    cursor.execute(sql_supplier_update, {"uuid_identification": uuid_identification})
    cursor.execute(sql_supplier_name_update, {"uuid_identification": uuid_identification})
    cursor.execute(sql_fac_update_except_edi, {"uuid_identification": uuid_identification})
    cursor.execute(sql_reference, {"uuid_identification": uuid_identification})
    cursor.execute(sql_cct, {"uuid_identification": uuid_identification})
    cursor.execute(sql_is_multi_store_true, {"uuid_identification": uuid_identification})
    cursor.execute(sql_is_multi_store_false, {"uuid_identification": uuid_identification})
    cursor.execute(sql_update_articles, {"uuid_identification": uuid_identification})
    cursor.execute(sql_alls_381, {"uuid_identification": uuid_identification})
    cursor.execute(sql_vat_regime, {"uuid_identification": uuid_identification})
    cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
    cursor.execute(vat_per_line, {"uuid_identification": uuid_identification})
    cursor.execute(sql_delta_vat, {"uuid_identification": uuid_identification})
    cursor.execute(sql_none, {"uuid_identification": uuid_identification})
    cursor.execute(sql_delivery_number, {"uuid_identification": uuid_identification})
    cursor.execute(sql_signboard, {"uuid_identification": uuid_identification})
    cursor.execute(sql_center, {"uuid_identification": uuid_identification})
    cursor.execute(sql_import_uuid_identification, {"uuid_identification": uuid_identification})
    cursor.execute(sql_purchase_vat_cee, {"uuid_identification": uuid_identification})
    cursor.execute(
        sql_validate,
        {"uuid_identification": uuid_identification, "created_by": get_user_automate()},
    )


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
        .values("invoice_number", "uuid_identification", *list(charges_dict))
        .annotate(dcount=Count("invoice_number"))
    )
    bulk_list = []

    for packaging_dict in packaging_amount_dict:
        edi = (
            EdiImport.objects.filter(
                invoice_number=packaging_dict.get("invoice_number"),
                uuid_identification=packaging_dict.get("uuid_identification"),
            )
            .filter(Q(valid=False) | Q(valid__isnull=True))
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
    sql_update = post_bulk_dict.get("sql_update")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def cosium_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Opto33 EDI
    :param uuid_identification: uuid_identification
    """
    sql_ttc_a_zero = post_cosium_dict.get("sql_ttc_a_zero")
    sql_totaux = post_cosium_dict.get("sql_totaux")
    sql_familles = post_cosium_dict.get("sql_familles")
    sql_origin = post_cosium_dict.get("sql_origin")
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_ttc_a_zero, {"uuid_identification": uuid_identification})
        cursor.execute(sql_familles, {"uuid_identification": uuid_identification})
        cursor.execute(sql_origin, {"uuid_identification": uuid_identification})
        cursor.execute(sql_totaux, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def cosium_achats_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Opto33 EDI
    :param uuid_identification: uuid_identification
    """
    sql_ttc_a_zero = post_cosium_achats_dict.get("sql_ttc_a_zero")
    sql_totaux = post_cosium_achats_dict.get("sql_totaux")
    sql_familles = post_cosium_achats_dict.get("sql_familles")
    sql_origin = post_cosium_achats_dict.get("sql_origin")
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_ttc_a_zero, {"uuid_identification": uuid_identification})
        cursor.execute(sql_familles, {"uuid_identification": uuid_identification})
        cursor.execute(sql_origin, {"uuid_identification": uuid_identification})
        cursor.execute(sql_totaux, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def tansferts_cosium_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Opto33 EDI
    :param uuid_identification: uuid_identification
    """
    sql_code_maison = post_transfert_cosium_dict.get("sql_code_maison")
    sql_amounts = post_transfert_cosium_dict.get("sql_amounts")
    sql_articles_cosium = post_transfert_cosium_dict.get("sql_articles_cosium")
    sql_articles_cosium_acuitis = post_transfert_cosium_dict.get("sql_articles_cosium_acuitis")
    sql_articles_base_cosium = post_transfert_cosium_dict.get("sql_articles_base_cosium")
    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_code_maison, {"uuid_identification": uuid_identification})
        cursor.execute(sql_amounts, {"uuid_identification": uuid_identification})
        cursor.execute(sql_articles_cosium, {"uuid_identification": uuid_identification})
        cursor.execute(sql_articles_cosium_acuitis, {"uuid_identification": uuid_identification})
        cursor.execute(sql_articles_base_cosium, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def edi_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Opto33 EDI
    :param uuid_identification: uuid_identification
    """

    sql_col_essilor = post_edi_dict.get("sql_col_essilor")
    sql_tva = post_edi_dict.get("sql_tva")
    sql_precilens = post_edi_dict.get("sql_precilens")
    sql_fac_update_edi = post_edi_dict.get("sql_fac_update_edi")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_col_essilor, {"uuid_identification": uuid_identification})
        cursor.execute(sql_tva, {"uuid_identification": uuid_identification})
        cursor.execute(sql_precilens, {"uuid_identification": uuid_identification})
        cursor.execute(sql_fac_update_edi, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def edi_trace_supplier_insert():
    """Update des traces pour avoir le nom du fournisseur dans les edi"""
    sql_edi_generique = post_edi_dict.get("sql_edi_generique")
    sql_get_edi = post_edi_dict.get("sql_get_edi")

    with connection.cursor() as cursor:
        cursor.execute(sql_get_edi)

        edi_flow = cursor.fetchall()

        for (uuid_identification,) in edi_flow:
            cursor.execute(sql_edi_generique, {"uuid_identification": uuid_identification})


def bbgr_statment_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Statment
    :param uuid_identification: uuid_identification
    """
    sql_vat = bbgr_002_statment_dict.get("sql_vat")
    sql_familles = bbgr_002_statment_dict.get("sql_familles")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        cursor.execute(sql_familles, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def bbgr_monthly_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Statment
    :param uuid_identification: uuid_identification
    """
    sql_vat = bbgr_003_monthly_dict.get("sql_vat")
    sql_familles = bbgr_002_statment_dict.get("sql_familles")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        cursor.execute(sql_familles, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def bbgr_retours_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Statment
    :param uuid_identification: uuid_identification
    """
    sql_vat = bbgr_004_retours_dict.get("sql_vat")
    sql_vat_amount = bbgr_004_retours_dict.get("sql_vat_amount")
    sql_total_amount_by_invoices = bbgr_004_retours_dict.get("sql_total_amount_by_invoices")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat_amount, {"uuid_identification": uuid_identification})
        cursor.execute(sql_total_amount_by_invoices, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def bbgr_reception_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Statment
    :param uuid_identification: uuid_identification
    """
    sql_vat = bbgr_005_receptions_dict.get("sql_vat")
    sql_vat_amount = bbgr_005_receptions_dict.get("sql_vat_amount")
    sql_total_amount_by_invoices = bbgr_005_receptions_dict.get("sql_total_amount_by_invoices")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat_amount, {"uuid_identification": uuid_identification})
        cursor.execute(sql_total_amount_by_invoices, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def eye_confort_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param uuid_identification: uuid_identification
    """
    sql_update = post_eye_dict.get("sql_update")
    sql_update_units = post_eye_dict.get("sql_update_units")
    sql_familles = post_eye_dict.get("sql_familles")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        cursor.execute(sql_familles, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def generique_post_insert(uuid_identification: AnyStr, post=None):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param uuid_identification: uuid_identification
    :param post: si l'on veut appliquer le post général
    """
    sql_update = post_generic_dict.get("sql_update")
    sql_net_amount_mgdev = post_generic_dict.get("sql_net_amount_mgdev")
    sql_vat = post_generic_dict.get("sql_vat")
    # sql_maison = post_generic_dict.get("sql_maison")
    sql_mg_developpemnt = post_generic_dict.get("sql_mg_developpemnt")
    sql_edi_generique = post_generic_dict.get("sql_edi_generique")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount_mgdev, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        # cursor.execute(sql_maison, {"uuid_identification": uuid_identification})
        cursor.execute(sql_mg_developpemnt, {"uuid_identification": uuid_identification})
        cursor.execute(sql_edi_generique, {"uuid_identification": uuid_identification})

        if post is None:
            post_general(uuid_identification, cursor)


def generique_post_insert_internal(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier EyeConfort
    :param uuid_identification: uuid_identification
    """
    sql_vat = post_generic_internal_dict.get("sql_vat")
    sql_update = post_generic_internal_dict.get("sql_update")
    sql_update_bu = post_generic_internal_dict.get("sql_update_bu")

    with connection.cursor() as cursor:
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_bu, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def hearing_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Hearing
    :param uuid_identification: uuid_identification
    """
    sql_update = post_hearing_dict.get("sql_update")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def interson_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Interson
    :param uuid_identification: uuid_identification
    """
    sql_update = post_interson_dict.get("sql_update")
    sql_bl_date = post_interson_dict.get("sql_bl_date")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_bl_date, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def johnson_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier JOHNSON
    :param uuid_identification: uuid_identification
    """
    sql_update = post_johnson_dict.get("sql_update")
    sql_update_vat_rate = post_johnson_dict.get("sql_update_vat_rate")
    sql_update_units = post_johnson_dict.get("sql_update_units")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_vat_rate, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def lmc_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier LMC
    :param uuid_identification: uuid_identification
    """
    sql_update = post_lmc_dict.get("sql_update")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def newson_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = post_newson_dict.get("sql_update")
    sql_round_net_amount = post_newson_dict.get("sql_round_net_amount")
    sql_net_amount = post_newson_dict.get("sql_net_amount")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_round_net_amount, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def phonak_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Phonak
    :param uuid_identification: uuid_identification
    """
    sql_update = post_phonak_dict.get("sql_update")
    sql_net_amount = post_phonak_dict.get("sql_net_amount")
    sql_mulitiple_dates = post_phonak_dict.get("sql_mulitiple_dates")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount, {"uuid_identification": uuid_identification})
        cursor.execute(sql_mulitiple_dates, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def prodition_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier Prodition
    :param uuid_identification: uuid_identification
    """
    sql_libele = post_prodition_dict.get("sql_libele")
    sql_update = post_prodition_dict.get("sql_update")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_libele, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def signia_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier SIGNA
    :param uuid_identification: uuid_identification
    """
    sql_update = post_signia_dict.get("sql_update")
    sql_update_units = post_signia_dict.get("sql_update_units")
    sql_update_bl = post_signia_dict.get("sql_update_bl")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_bl, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def starkey_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = post_starkey_dict.get("sql_update")
    sql_copie_envoi_depot = post_starkey_dict.get("sql_copie_envoi_depot")
    sql_delete_envoi_depot = post_starkey_dict.get("sql_delete_envoi_depot")
    sql_update_units = post_starkey_dict.get("sql_update_units")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_copie_envoi_depot, {"uuid_identification": uuid_identification})
        cursor.execute(sql_delete_envoi_depot, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def technidis_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = post_technidis_dict.get("sql_update")
    sql_update_units = post_technidis_dict.get("sql_update_units")
    sql_net_amount = post_technidis_dict.get("sql_net_amount")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        cursor.execute(sql_net_amount, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def unitron_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier NEWSON
    :param uuid_identification: uuid_identification
    """
    sql_update = post_unitron_dict.get("sql_update")
    sql_mulitiple_dates = post_unitron_dict.get("sql_mulitiple_dates")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_mulitiple_dates, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def widex_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier WIDEX
    :param uuid_identification: uuid_identification
    """
    sql_update = post_widex_dict.get("sql_update")
    sql_update_units = post_widex_dict.get("sql_update_units")
    sql_invoices_amounts = post_widex_dict.get("sql_invoices_amounts")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update_units, {"uuid_identification": uuid_identification})
        cursor.execute(sql_invoices_amounts, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)


def widexga_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier WIDEX GA
    :param uuid_identification: uuid_identification
    """
    widex_post_insert(uuid_identification)


def z_bu_refac_post_insert(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier issu de la requête Sage pour la BU REFAC0
    :param uuid_identification: uuid_identification
    """
    sql_update = post_z_bu_refac.get("sql_update")
    sql_piece = post_z_bu_refac.get("sql_piece")
    sql_name = post_z_bu_refac.get("sql_name")
    sql_vat = post_z_bu_refac.get("sql_vat")

    with connection.cursor() as cursor:
        cursor.execute(SQL_QTY, {"uuid_identification": uuid_identification})
        cursor.execute(sql_update, {"uuid_identification": uuid_identification})
        cursor.execute(sql_piece, {"uuid_identification": uuid_identification})
        cursor.execute(sql_name, {"uuid_identification": uuid_identification})
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)
