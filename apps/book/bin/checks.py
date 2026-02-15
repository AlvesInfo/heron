# pylint: disable=C0303,E0401,W0212
"""Module de vérifications pour l'app book

Commentaire:

created at: 2022-12-14
created by: Paulo ALVES

modified at:
modified by:
"""
import os
import platform
import sys

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from psycopg2 import sql
from django.db import connection

from apps.core.functions.functions_postgresql import query_dict
from apps.accountancy.models import CctSage
from apps.book.models import SupplierCct
from apps.book.forms import SageEmailForm
from apps.core.bin.notifications import broadcast_notification


def check_cct_identifier(cleaned_data: dict):
    """Vérification que l'identifiant saisi n'existe pas déjà dans un autre cct ou dans le même
    :param cleaned_data: les données du formulaire après validation du formulaire par django
    :return: message
    """
    before_cct_identifier = cleaned_data.get("id").cct_identifier

    if before_cct_identifier:
        before_cct_identifier = (
            before_cct_identifier[:-1]
            if before_cct_identifier[-1] == "|"
            else before_cct_identifier
        )
    else:
        before_cct_identifier = ""

    before = str(before_cct_identifier).split("|")

    after_cct_identifier = cleaned_data.get("cct_identifier")

    if after_cct_identifier:
        after_cct_identifier = (
            after_cct_identifier[:-1] if after_cct_identifier[-1] == "|" else after_cct_identifier
        )

    after = str(after_cct_identifier).split("|")

    if before == after:
        message = "Vous n'avez rien modifié !"
        return False, message

    if set(before) == set(after):
        message = (
            "Vous avez ajouté un dentifiant déjà présent pour le cct : "
            f"{cleaned_data.get('id').cct_uuid_identification.cct}"
        )
        return False, message

    diff_identifier = list(set(after).difference(set(before)))

    # On vérifie si l'identifiant pour le cct existe déjà
    with connection.cursor() as cursor:
        sql_verify = sql.SQL(
            """
            select 
                    cct, cct_identifier
            from (
                select
                       third_party_num, 
                       ac.cct ,
                       unnest(
                            string_to_array(
                                case 
                                    when right("cct_identifier", 1) = '|' 
                                    then left("cct_identifier", length("cct_identifier")-1) 
                                    else "cct_identifier"
                                end
                                , 
                                '|'
                            )
                       ) as cct_identifier
                from {table_supplier} bs
                join {table_cct} ac 
                on bs.cct_uuid_identification = ac.uuid_identification 
                where third_party_num = %(third_party_num)s
            ) ident 
            where cct_identifier = ANY(%(cct_identifier)s)
            """
        ).format(
            table_supplier=sql.Identifier(SupplierCct._meta.db_table),
            table_cct=sql.Identifier(CctSage._meta.db_table),
        )
        cursor.execute(
            sql_verify,
            {
                "third_party_num": cleaned_data.get("id").third_party_num.third_party_num,
                "cct_identifier": diff_identifier,
            },
        )
        ident_list = cursor.fetchall()

        if ident_list:
            message = ""

            for cct, ident in ident_list:
                message += f"L'identifiant {ident} est déjà utilisé dans le cct {cct}   -   "

            message = message[:-7]

            return None, message

    return True, ""


def check_emails_to_send():
    """Retourne les faux emails, avant envoi par mail des factures"""

    sql_check_emails = """
    select 
        email, third_party_num 
    from (
        select 
            email_01 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_02 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_03 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_04 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_05 as email, third_party_num
        from book_society bs 
    ) r
    where r.email is not null and r.email != ''
    and exists (
        select 1 
        from "invoices_saleinvoice" "si" 
        where not si."final" and r.third_party_num = si.third_party_num  
    )
    order by r.third_party_num, r.email
    """

    emails_errors_list = query_dict(connection, sql_check_emails)

    for email_dict in emails_errors_list:
        if not SageEmailForm(data=email_dict).is_valid():
            yield email_dict

        else:
            continue


def check_emails(is_loop=False):
    """Vérifie les email_01 à email_05 présents dans book society"""

    sql_check_emails = """
    select 
        email, third_party_num 
    from (
        select 
            email_01 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_02 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_03 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_04 as email, third_party_num
        from book_society bs 
        union all
        select 
            email_05 as email, third_party_num
        from book_society bs 
    ) r
    where r.email is not null and r.email != ''
    order by r.third_party_num, r.email
    """

    emails_errors_list = query_dict(connection, sql_check_emails)
    errors = False

    for email_dict in emails_errors_list:
        if not SageEmailForm(data=email_dict).is_valid():

            if not errors and is_loop:
                # If error Notify in front mails errors
                broadcast_notification(
                    title="Erreurs Emails",
                    message="Les emails des Tiers Sage X3 contiennent des erreurs !",
                    level="error",
                    link="/book/emails_errors_list/"
                )

            errors = True

            yield email_dict


def check_emails_notifications():
    """Set les faux emails en appelant la fonction check_emails()"""
    for _ in check_emails(is_loop=True):
        ...


if __name__ == "__main__":
    """
    # for emails in check_emails_to_send():
    #     print(emails)
    #
    # for emails in check_emails():
    #     print(emails)
    """
    check_emails_notifications()
