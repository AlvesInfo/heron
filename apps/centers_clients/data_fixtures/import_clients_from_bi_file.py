import os
import platform
import sys
import csv
from pathlib import Path

from django.db import transaction


import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from apps.core.functions.functions_setups import settings
from apps.accountancy.models import AccountSage, CodePlanSage, CctSage
from apps.book.models import Society
from apps.centers_clients.models import Maison, MaisonBi
from apps.centers_clients.forms import ImportMaisonBiForm, MaisonImportForm


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
            if i > 0:
                (
                    code_maison,
                    cct,
                    third_party_num,
                    sage_vat_by_default,
                    center_purchase,
                    sign_board,
                    integrable,
                    chargeable,
                    credit_account,
                    debit_account,
                    opening_date,
                    immeuble,
                    adresse,
                    code_postal,
                    ville,
                    email,
                    pays,
                    intitule,
                    intitule_court,
                    client_familly,
                ) = row
                credit_account = AccountSage.objects.get(account=credit_account).uuid_identification
                debit_account = AccountSage.objects.get(account=debit_account).uuid_identification

                initials = {}

                if code_maison:
                    libelle = "depuis B.I : "
                    form = ImportMaisonBiForm(
                        {"maison_bi": code_maison, "cct": cct, "tiers": third_party_num}
                    )
                    if form.is_valid():
                        society = Society.objects.get(
                            third_party_num=form.cleaned_data.get("tiers")
                        )
                        maison_bi = MaisonBi.objects.get(
                            code_maison=form.cleaned_data.get("maison_bi")
                        )
                        cct = CctSage.objects.get(cct=form.cleaned_data.get("cct"))

                        form_bi = MaisonImportForm(
                            {
                                "code_maison": maison_bi.code_maison,
                                "cct": cct,
                                "third_party_num": society,
                                "intitule": maison_bi.intitule,
                                "intitule_court": maison_bi.intitule_court
                                or maison_bi.intitule[:12],
                                "code_cosium": maison_bi.code_cosium,
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
                                "sage_vat_by_default": sage_vat_by_default,
                                "center_purchase": center_purchase,
                                "sign_board": sign_board,
                                "integrable": integrable,
                                "chargeable": chargeable,
                                "credit_account": credit_account,
                                "debit_account": debit_account,
                                "client_familly": client_familly,
                                "signature_franchise_date": maison_bi.opening_date,
                                "sage_plan_code": code_plan_sage,
                            }
                        )
                        if form_bi.is_valid():
                            initials = form_bi.cleaned_data
                            print("initials dans bi : ", initials)
                        else:
                            print(libelle, cct, " - form_bi : ", form_bi.errors)
                else:
                    libelle = "direct     : "
                    form = MaisonImportForm(
                        {
                            "code_maison": code_maison,
                            "cct": cct,
                            "third_party_num": third_party_num,
                            "intitule": intitule,
                            "intitule_court": intitule_court[:20] or intitule[:20],
                            "code_cosium": None,
                            "code_bbgr": None,
                            "opening_date": opening_date,
                            "closing_date": None,
                            "immeuble": immeuble,
                            "adresse": adresse,
                            "code_postal": code_postal,
                            "ville": ville,
                            "pays": pays,
                            "telephone": None,
                            "email": email.split(";")[0],
                            "sage_vat_by_default": sage_vat_by_default,
                            "center_purchase": center_purchase,
                            "sign_board": sign_board,
                            "integrable": integrable,
                            "chargeable": chargeable,
                            "credit_account": credit_account,
                            "debit_account": debit_account,
                            "client_familly": client_familly,
                            "signature_franchise_date": opening_date,
                            "sage_plan_code": code_plan_sage,
                        }
                    )

                    if form.is_valid():
                        initials = form.cleaned_data

                        print("initials dans bi : ", initials)
                    else:
                        print(libelle, cct, " - from : ", form.errors)

                if initials:
                    Maison.objects.create(**initials)


if __name__ == "__main__":
    csv_file = Path(settings.APPS_DIR) / "centers_clients/data_fixtures/import_bi_access.csv"
    print(csv_file)
    import_file(csv_file)
