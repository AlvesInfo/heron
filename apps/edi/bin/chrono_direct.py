from pathlib import Path
import csv
from decimal import Decimal

from django.db import transaction

from apps.core.functions.functions_setups import settings
from apps.centers_clients.models import Maison


@transaction.atomic
def set_generique_chrono_direct(file_path, interne_file_path, dte_fac):
    """Table pour génération des factures chronodirect"""

    base_dict = {
        "fournisseur": "CHRONODIRECT",
        "siret_fournisseur": "43158017400024",
        "siret_payeur": "51778087000096",
        "code_fournisseur": "CHRO002",
        "code_maison": "",
        "maison": "",
        "num_commande": "",
        "date_commande": "",
        "num_bl": "",
        "date_bl": "",
        "num_facture": "",
        "date_facture": "",
        "date_echeance": "",
        "nature_facture": "FA",
        "devise": "EUR",
        "reference_article": "",
        "code_ean": "",
        "libelle": "",
        "famille": "COMMUNICATION",
        "qte": "",
        "px_unitaire_brut": "",
        "px_unitaire_net": "",
        "montant_brut": "",
        "montant_remise": "",
        "montant_net": "",
        "taux_tva": "2000",
        "montant_tva": "",
        "montant_ttc": "",
        "nom_client": "",
        "num_serie": "",
        "Commentaire": "",
    }

    reference_dict = {
        item.reference_cosium: item.cct.cct for item in Maison.objects.using("heron").all()
    }

    with (
        file_path.open("r", encoding="cp1252") as file,
        interne_file_path.open("w", encoding="utf8") as interne_file,
    ):
        csv_reader = csv.reader(file, delimiter=";", quotechar='"')
        interne_writer = csv.writer(
            interne_file,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
        )
        interne_writer.writerow(base_dict.keys())

        for line in csv_reader:
            maison = line[1]
            qty = Decimal(line[2].replace(",", "."))
            mont_cession = Decimal(line[4].replace(",", "."))

            if reference_dict.get(maison) is None:
                raise Exception(
                    f"La référence cosium dans les client n'exite pas({maison})"
                )

            base_dict["code_maison"] = reference_dict.get(maison)
            base_dict["maison"] = maison
            base_dict["date_facture"] = dte_fac
            base_dict["date_echeance"] = dte_fac
            base_dict["reference_article"] = (
                "courrier audio" if "audio" in line[0] else "courrier_optique"
            )
            base_dict["libelle"] = line[0]
            base_dict["qte"] = qty
            base_dict["px_unitaire_brut"] = round(mont_cession/qty, 2)
            base_dict["px_unitaire_net"] = round(mont_cession/qty, 2)
            base_dict["montant_brut"] = round(mont_cession, 2)
            base_dict["montant_remise"] = 0
            base_dict["montant_net"] = round(mont_cession, 2)
            base_dict["montant_tva"] = round(round(mont_cession, 2) * Decimal("0.2"), 2)
            base_dict["montant_ttc"] = (
                    round(round(mont_cession, 2) * Decimal("0.2"), 2) + round(mont_cession, 2)
            )
            base_dict["num_facture"] = f"GENERIQUE_INTERNAL_CHRONODIRECT_{dte_fac}"

            interne_writer.writerow(base_dict.values())

    print("Le fichier à bien été créé")


if __name__ == "__main__":
    file_path = Path(r"/Users/paulo/Downloads/Chronodirect_Septembre_2025.csv")
    interne_file_path = Path(r"/Users/paulo/Downloads/generique_interne_chronodirect.csv")
    set_generique_chrono_direct(file_path, interne_file_path, dte_fac="20250930")
