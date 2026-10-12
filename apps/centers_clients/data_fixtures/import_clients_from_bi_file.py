import os
import platform
import sys
import csv
from pathlib import Path

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db import transaction

from apps.core.functions.functions_setups import settings
from apps.accountancy.models import AccountSage, CodePlanSage, CctSage
from apps.book.models import Society
from apps.centers_clients.models import Maison, MaisonBi
from apps.centers_clients.forms import ImportMaisonBiForm, MaisonImportForm
from heron.loggers import LOGGER_IMPORT


# Colonnes du fichier csv, dans l'ordre
ROW_FIELDS = (
    "code_maison",
    "cct",
    "third_party_num",
    "sage_vat_by_default",
    "center_purchase",
    "sign_board",
    "integrable",
    "chargeable",
    "credit_account",
    "debit_account",
    "opening_date",
    "immeuble",
    "adresse",
    "code_postal",
    "ville",
    "email",
    "pays",
    "intitule",
    "intitule_court",
    "client_familly",
)
# Colonnes du fichier reprises telles quelles dans le formulaire de la maison
COMMON_FIELDS = (
    "sage_vat_by_default",
    "center_purchase",
    "sign_board",
    "integrable",
    "chargeable",
    "credit_account",
    "debit_account",
    "client_familly",
)


def _initials_from_bi(line: dict, code_plan_sage: CodePlanSage) -> dict:
    """
    Données de la maison reprises de la B.I (ligne avec un code maison) : vide si le trio
    maison B.I / cct / tiers ou le formulaire de la maison sont invalides
    :param line: ligne du fichier, par nom de colonne
    :param code_plan_sage: plan de comptes Sage de la maison
    """
    form = ImportMaisonBiForm(
        {"maison_bi": line["code_maison"], "cct": line["cct"], "tiers": line["third_party_num"]}
    )

    if not form.is_valid():
        return {}

    society = Society.objects.get(third_party_num=form.cleaned_data.get("tiers"))
    maison_bi = MaisonBi.objects.get(code_maison=form.cleaned_data.get("maison_bi"))
    cct = CctSage.objects.get(cct=form.cleaned_data.get("cct"))

    form_bi = MaisonImportForm(
        {
            "code_maison": maison_bi.code_maison,
            "cct": cct,
            "third_party_num": society,
            "intitule": maison_bi.intitule,
            "intitule_court": maison_bi.intitule_court or maison_bi.intitule[:12],
            "code_cosium": maison_bi.code_cosium,
            "reference_cosium": maison_bi.reference_cosium,
            "code_bbgr": maison_bi.code_bbgr,
            "opening_date": maison_bi.opening_date,
            "closing_date": maison_bi.closing_date,
            "immeuble": maison_bi.immeuble,
            "adresse": maison_bi.adresse or "_",
            "code_postal": maison_bi.code_postal or "_",
            "ville": maison_bi.ville or "_",
            "pays": maison_bi.pays,
            "telephone": maison_bi.telephone,
            "email": maison_bi.email,
            **{field: line[field] for field in COMMON_FIELDS},
            "signature_franchise_date": maison_bi.opening_date,
            "sage_plan_code": code_plan_sage,
        }
    )

    if not form_bi.is_valid():
        LOGGER_IMPORT.info("%s %s %s %s", "depuis B.I : ", cct, ' - form_bi : ', form_bi.errors)
        return {}

    LOGGER_IMPORT.info("%s %s", 'initials dans bi : ', form_bi.cleaned_data)

    return form_bi.cleaned_data


def _initials_direct(line: dict, code_plan_sage: CodePlanSage) -> dict:
    """
    Données de la maison prises directement dans le fichier (ligne sans code maison) : vide si
    le formulaire de la maison est invalide
    :param line: ligne du fichier, par nom de colonne
    :param code_plan_sage: plan de comptes Sage de la maison
    """
    form = MaisonImportForm(
        {
            "code_maison": line["code_maison"],
            "cct": line["cct"],
            "third_party_num": line["third_party_num"],
            "intitule": line["intitule"],
            "intitule_court": line["intitule_court"][:20] or line["intitule"][:20],
            "code_cosium": None,
            "reference_cosium": None,
            "code_bbgr": None,
            "opening_date": line["opening_date"],
            "closing_date": None,
            "immeuble": line["immeuble"],
            "adresse": line["adresse"],
            "code_postal": line["code_postal"],
            "ville": line["ville"],
            "pays": line["pays"],
            "telephone": None,
            "email": line["email"].split(";")[0],
            **{field: line[field] for field in COMMON_FIELDS},
            "signature_franchise_date": line["opening_date"],
            "sage_plan_code": code_plan_sage,
        }
    )

    if not form.is_valid():
        LOGGER_IMPORT.info("%s %s %s %s", "direct     : ", line["cct"], ' - from : ', form.errors)
        return {}

    LOGGER_IMPORT.info("%s %s", 'initials dans bi : ', form.cleaned_data)

    return form.cleaned_data


@transaction.atomic
def import_file(file_path: Path):
    """Import de maison depuis un fichier csv
    :param file_path: chemin du fichier
    :return: None
    """
    code_plan_sage = CodePlanSage.objects.get(code_plan_sage="FRA")

    with file_path.open() as file:
        csv_reader = csv.reader(
            file,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_MINIMAL,
        )

        for i, row in enumerate(csv_reader):
            if i == 0:
                continue

            line = dict(zip(ROW_FIELDS, row, strict=True))
            line["credit_account"] = AccountSage.objects.get(
                account=line["credit_account"]
            ).uuid_identification
            line["debit_account"] = AccountSage.objects.get(
                account=line["debit_account"]
            ).uuid_identification

            if line["code_maison"]:
                initials = _initials_from_bi(line, code_plan_sage)
            else:
                initials = _initials_direct(line, code_plan_sage)

            if initials:
                Maison.objects.create(**initials)


if __name__ == "__main__":
    csv_file = Path(settings.APPS_DIR) / "centers_clients/data_fixtures/import_bi_access.csv"
    print(csv_file)
    import_file(csv_file)
