# pylint: disable=E0401,R0913,W0212
"""
FR : Module des outils de gestion de l'application edi
EN : Edi application management tools module

Commentaire:

created at: 2023-01-18
created by: Paulo ALVES

modified at: 2023-01-18
modified by: Paulo ALVES
"""
import inspect
from typing import AnyStr

from django.db import connection
from django.utils import timezone

from apps.core.models import ChangesTrace
from apps.data_flux.models import Trace
from apps.users.models import User
from apps.edi.models import EdiImport


def get_sens(sens: str):
    """Retourne le sens de facturation AC, AC/VE, VE"""
    if sens == "2":
        return {"purchase_invoice": "true", "sale_invoice": "true"}

    if sens == "1":
        return {"purchase_invoice": "false", "sale_invoice": "true"}

    return {"purchase_invoice": "true", "sale_invoice": "false"}


def set_trace_hand_invoice(
    invoice_category: AnyStr,
    invoice_number: AnyStr,
    user: User,
    edi_objects: EdiImport.objects = None,
    numbers: int = 0,
    errors: bool = False,
):
    """
    Création des traces et log
    :param invoice_category: catégorie ( marchandises, formations, personnel)
    :param invoice_number: N° de Facture
    :param user: User faisant la création
    :param edi_objects: Lignes de factures Créées
    :param numbers: Nombre de factures saisies
    :param errors: si il a eu des erreurs
    :return:
    """
    function_call = str(inspect.currentframe().f_back)[:255]
    Trace.objects.create(
        trace_name=f"Saisie Facture de {invoice_category.capitalize()}",
        file_name=f"Ecran de saisie : edi/create_hand_invoices/{invoice_category}/",
        application_name="set_hand_invoice",
        flow_name="Saisie",
        errors=errors,
        comment=f"Saisie de la facture N° {invoice_number}",
        created_numbers_records=numbers,
        updated_numbers_records=0,
        errors_numbers_records=0,
        unknown_numbers_records=0,
        created_by=user,
    )

    # S'il n'y a pas d'erreurs alors on crée la change_trace
    if not errors:
        for edi_line in edi_objects:
            after_dict = {
                key: value for key, value in edi_line.__dict__.items() if key != "_state" and value
            }
            ChangesTrace.objects.create(
                action_datetime=timezone.now(),
                action_type=1,
                function_name=function_call,
                action_by=user,
                before={},
                after=after_dict,
                difference={"avant": {}, "après": after_dict},
                model_name=EdiImport._meta.model_name,
                model=EdiImport._meta.model,
                db_table=EdiImport._meta.db_table,
            )


def delete_orphans_controls():
    """
    Supprime tous les Contrôles edi_ediimport_control orphelins.
    Ceux qui ne sont pas dans edi_ediimport et ceux qui ne sont pas dans invoives_invoice
    :return:
    """
    with connection.cursor() as cursor:
        sql_delete = """
        delete from "edi_ediimportcontrol" "edic"
        where not exists (
            select 1 from (
                select 
                    "uuid_control" 
                from "edi_ediimport" "ee" 
                group by "uuid_control"
                union all 
                select 
                    "uuid_control" 
                from "invoices_invoice" "ii"  
                group by "uuid_control"
            ) "alls"
            where "alls"."uuid_control" = "edic"."uuid_identification" 
        ) 
        """
        cursor.execute(sql_delete)
