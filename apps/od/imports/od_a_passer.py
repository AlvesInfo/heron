# pylint: disable=E0401,R0912,R0913,R0914,R0915,W0703,W1203
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2025-03-15
created by: Paulo ALVES

modified at: 2025-03-15
modified by: Paulo ALVES
"""

from pathlib import Path

from django.utils import timezone
from django.db import connection
from django.db.models import F, ExpressionWrapper, CharField, Value, Func, Q

from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.od.models import ModelOd
from apps.od.forms.forms_djantic.djantic_od import OdSchema
from apps.data_flux.trace import get_trace
from apps.parameters.models import Counter
from apps.parameters.bin.core import get_counter_num


proccessing_dir = Path(settings.PROCESSING_OD_A_PASSER)


def import_od_a_passer(file_path: Path):
    """
    Import du fichier des comptes comptable Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = ModelOd
    validator = OdSchema
    file_name = file_path.name
    trace_name = "Import od à passer"
    application_name = "import_od_a_passer"
    flow_name = "ModelOd"
    comment = f"import du fichier {file_name}, des OD à passer"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(
        model,
        flow_name,
        file_path,
        trace,
        validator,
        params_dict_loader,
        insert_mode="insert",
    )

    return trace, to_print


def validation_amounts(error, message):
    """
    Validation des sommes des montants HT et TVA pour vérifier qu'ils soient égaux au montant ttc
    :param error: Erreur (booléen)
    :param message: Message à renvoyer
    """
    # Concaténation des champs pour recréer l'expression `delta`
    delta_expression = ExpressionWrapper(
        Func(
            F("libelle"),
            Value(" : ("),
            F("montant_ht"),
            Value(" + "),
            F("montant_tva"),
            Value(") - ("),
            F("montant_ttc"),
            Value(")"),
            function="CONCAT",
        ),
        output_field=CharField(),
    )

    # Filtre pour la condition WHERE
    queryset = ModelOd.objects.annotate(delta=delta_expression).filter(
        ~Q(montant_ttc=(F("montant_ht") + F("montant_tva")))
    )

    if queryset.exists():
        message = ""
        error = True

        for item in queryset[:30]:
            message += (
                f'<span>- la ligne "{item.delta}" est pas déséquilibrée</span><br>'
            )

    return error, message


def update_blank_account():
    """
    Mise à jour des colonnes compte_produit, compte_tva, compte_collectif,
    par un blank si les colonnes sont nulles
    """
    sql_update = """
    update "od_modelod"
    set "compte_produit" = case 
                            when "compte_produit" is null 
                            then '' 
                            else "compte_produit" 
                           end,
        "compte_tva" = case 
                        when "compte_tva" is null 
                        then '' 
                        else "compte_tva" 
                       end,
        "compte_collectif" = case 
                                when "compte_collectif" is null 
                                then '' 
                                else "compte_collectif" 
                             end
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_update)


def validation_accounts(error, message):
    """
    Validation que les comptes comptable Sage X3 existent bien
    :param error: Erreur (booléen)
    :param message: Message à renvoyer
    """
    sql_verif_accounts = """
    with "all_od_accounts" as (
        select 
            "id", 
            unnest(array["compte_produit", "compte_tva", "compte_collectif"]) as "account",
            "code_plan"
        from "od_modelod"
    )
    select 
        "odm"."id"
    from "all_od_accounts" "odm"
    left join "accountancy_accountsage" "aa" 
    on "aa"."code_plan_sage" = "odm"."code_plan"
    and "aa"."account" = "odm"."account"
    where "aa"."account" isnull
    """
    fake_accounts = set()

    with connection.cursor() as cursor:
        cursor.execute(sql_verif_accounts)
        fake_accounts = set([row[0] for row in cursor.fetchall()])

    if not fake_accounts:
        return error, message

    # Concaténation des champs pour recréer l'expression `account`
    delta_expression = ExpressionWrapper(
        Func(
            F("libelle"),
            Value(" : ("),
            F("montant_ht"),
            Value(" + "),
            F("montant_tva"),
            Value(") - ("),
            F("montant_ttc"),
            Value(") : compte_produit="),
            F("compte_produit"),
            Value(" : compte_tva="),
            F("compte_tva"),
            Value(" : compte_collectif="),
            F("compte_collectif"),
            function="CONCAT",
        ),
        output_field=CharField(),
    )

    # Filtre pour la condition WHERE
    queryset = ModelOd.objects.annotate(account=delta_expression).filter(
        pk__in=fake_accounts
    )

    if queryset.exists():
        message = ""
        error = True

        for item in queryset[:30]:
            message += f'<span>- la ligne "{item.account}" a un compte comptable qui est erroné</span><br>'

    return error, message


def validation_axes(error, message):
    """
    Validation que les axes Sage X3 existent bien
    :param error: Erreur (booléen)
    :param message: Message à renvoyer
    """
    sql_verif_axes = """
    with "all_od_axes" as (
        select 
            "id", 
            unnest(array["axe_bu", "axe_pro", "axe_prj", "axe_pys", "axe_rfa"]) as "axe"
        from "od_modelod"
    )
    select 
        "oda"."id"
    from "all_od_axes" "oda"
    left join "accountancy_sectionsage" "aa"
    on "aa"."section"  = "oda"."axe"
    where "aa"."section" isnull
    """
    fake_axes = set()

    with connection.cursor() as cursor:
        cursor.execute(sql_verif_axes)
        fake_axes = set([row[0] for row in cursor.fetchall()])

    if not fake_axes:
        return error, message

    # Concaténation des champs pour recréer l'expression `axes`
    delta_expression = ExpressionWrapper(
        Func(
            F("libelle"),
            Value(" : ("),
            F("montant_ht"),
            Value(" + "),
            F("montant_tva"),
            Value(") - ("),
            F("montant_ttc"),
            Value(") : axe_bu="),
            F("axe_bu"),
            Value(" : axe_pro="),
            F("axe_pro"),
            Value(" : axe_prj="),
            F("axe_prj"),
            Value(") : axe_pys="),
            F("axe_pys"),
            Value(" : axe_rfa="),
            F("axe_rfa"),
            function="CONCAT",
        ),
        output_field=CharField(),
    )

    # Filtre pour la condition WHERE
    queryset = ModelOd.objects.annotate(axes=delta_expression).filter(pk__in=fake_axes)

    if queryset.exists():
        message = ""
        error = True

        for item in queryset[:30]:
            message += (
                f'<span>- la ligne "{item.axes}" a un axe qui est erroné</span><br>'
            )

    return error, message


def validation_cct(error, message):
    """
    Validation que les cct existent bien
    :param error: Erreur (booléen)
    :param message: Message à renvoyer
    """
    sql_verif_axes = """
    select 
        "odm"."id"
    from "od_modelod" "odm"
    left join "accountancy_cctsage" "aa" 
    on "aa"."cct" = "odm"."cct"
    where "aa"."cct" isnull
    """
    fake_cct = set()

    with connection.cursor() as cursor:
        cursor.execute(sql_verif_axes)
        fake_cct = set([row[0] for row in cursor.fetchall()])

    if not fake_cct:
        return error, message

    # Concaténation des champs pour recréer l'expression `cct_false`
    delta_expression = ExpressionWrapper(
        Func(
            F("libelle"),
            Value(" : ("),
            F("montant_ht"),
            Value(" + "),
            F("montant_tva"),
            Value(") - ("),
            F("montant_ttc"),
            Value(") : cct="),
            F("cct"),
            function="CONCAT",
        ),
        output_field=CharField(),
    )

    # Filtre pour la condition WHERE
    queryset = ModelOd.objects.annotate(cct_false=delta_expression).filter(
        pk__in=fake_cct
    )

    if queryset.exists():
        message = ""
        error = True

        for item in queryset[:30]:
            message += f'<span>- la ligne "{item.cct_false}" a un cct qui est erroné</span><br>'

    return error, message


def validation_third_party_num(error, message):
    """
    Validation que les third_party_num (tiers) existent bien
    :param error: Erreur (booléen)
    :param message: Message à renvoyer
    """
    sql_verif_tiers = """
    select 
        "odm"."id"
    from "od_modelod" "odm"
    left join "book_society" "aa" 
    on "aa"."third_party_num" = "odm"."third_party_num"
    where "aa"."third_party_num" isnull
    """
    fake_tiers = set()

    with connection.cursor() as cursor:
        cursor.execute(sql_verif_tiers)
        fake_tiers = set([row[0] for row in cursor.fetchall()])

    if not fake_tiers:
        return error, message

    # Concaténation des champs pour recréer l'expression `tiers_false`
    delta_expression = ExpressionWrapper(
        Func(
            F("libelle"),
            Value(" : ("),
            F("montant_ht"),
            Value(" + "),
            F("montant_tva"),
            Value(") - ("),
            F("montant_ttc"),
            Value(") : third_party_num="),
            F("third_party_num"),
            function="CONCAT",
        ),
        output_field=CharField(),
    )

    # Filtre pour la condition WHERE
    queryset = ModelOd.objects.annotate(tiers_false=delta_expression).filter(
        pk__in=fake_tiers
    )

    if queryset.exists():
        message = ""
        error = True

        for item in queryset[:30]:
            message += f'<span>- la ligne "{item.tiers_false}" a un tiers qui est erroné</span><br>'

    return error, message


def update_blank_facture_heron():
    """Mise à jour de la colonne facture_heron, par un blank si la colonne est nulle"""
    sql_update = """
    update "od_modelod"
    set "facture_heron" = case 
                            when "facture_heron" is null 
                            then '' 
                            else "facture_heron" 
                           end
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_update)


def set_base_sage_invoice_number():
    """On va setter un n° de pièce sage pour les exports sage"""
    sql_invoices_number = """
    select 
        "facture_heron"
    from "od_modelod"
    group by "facture_heron"
    """
    counter = Counter.objects.get(name="generic")

    with connection.cursor() as cursor:
        cursor.execute(sql_invoices_number)
        invoicess = [row[0] for row in cursor.fetchall()]

        for invoice_number in invoicess:
            if not invoice_number or len(invoice_number) < 12:
                base_sage_number = get_counter_num(counter_instance=counter)
            else:
                base_sage_number = invoice_number[2:]

            base_sage_number = base_sage_number[-12:]

            sql_upadte = """
            update "od_modelod"
            set "base_sage_invoice_number" = %(base_sage_number)s
            where "facture_heron" = %(invoice_number)s
            """
            cursor.execute(
                sql_upadte,
                {
                    "invoice_number": invoice_number,
                    "base_sage_number": base_sage_number,
                },
            )


def import_od_files():
    """Boucle d'import des fichiers pour générer les od"""
    # On efface d'abord les données de la table
    ModelOd.objects.all().delete()
    message = ""
    error = False

    for file_path in proccessing_dir.glob("*.csv"):
        _, to_print = import_od_a_passer(file_path)

        if "Pas d'erreurs" not in to_print:
            ModelOd.objects.all().delete()
            error = True
            message = (
                f'<span>- le fichier "{file_path.name}" '
                f"a générer une erreur veillez consulter les traces</span><br>"
            )
            return error, message

        message += (
            f"<span>- le fichier {file_path.name} a été intégrer avec succes</span><br>"
        )

    error, message = validation_amounts(error, message)

    if error:
        return error, message

    update_blank_account()
    set_base_sage_invoice_number()

    error, message = validation_accounts(error, message)

    if error:
        return error, message

    error, message = validation_axes(error, message)

    if error:
        return error, message

    error, message = validation_cct(error, message)

    if error:
        return error, message

    error, message = validation_third_party_num(error, message)

    return error, message


if __name__ == "__main__":
    # print(import_od_files())
    set_base_sage_invoice_number()
