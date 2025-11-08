from pathlib import Path
import csv
from decimal import Decimal

import psycopg2
from psycopg2.extensions import parse_dsn


def cnx_postgresql(string_of_connexion):
    """
    Fonction de connexion à Postgresql par psycopg2
        :param string_of_connexion: cnx_string = (
                                        f"dbname={NAME_DATABASE} "
                                        f"user={USER_DATABASE} "
                                        f"password={PASSWORD_DATABASE} "
                                        f"host={HOST_DATABASE} "
                                        f"port={PORT_DATABASE}"
                                    )
        :return: cnx
    """
    try:
        kwargs_cnx = parse_dsn(string_of_connexion)
        connexion = psycopg2.connect(**kwargs_cnx)

    except psycopg2.Error as except_error:
        log_line = f"cnx_postgresql error: {except_error}\n"
        print(log_line)
        connexion = None

    return connexion


def query_select(cnx, sql_requete=None, params=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql.
        :param cnx: Connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :param params: dictionnaire des paramètes à passer
        :return: La liste des éléments de la requête
    """
    if sql_requete:
        try:
            with cnx.cursor() as cur:
                if params:
                    cur.execute(sql_requete, params)
                else:
                    cur.execute(sql_requete)
                list_rows = cur.fetchall()
                # print(cur.mogrify(sql_requete, params).decode())
            return list_rows

        except psycopg2.Error as except_error:
            log_line = f"query_select error: {except_error}\n"
            print(log_line)
    return None


def set_generique_chrono_direct(cnx_dns, base_file_path, internal_file_path, dte_fac):
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

    with (
        cnx_postgresql(cnx_dns) as cnx,
        base_file_path.open("r", encoding="cp1252") as file,
        internal_file_path.open("w", encoding="utf8") as interne_file,
    ):
        query = query_select(
            cnx,
            sql_requete='select "reference_cosium", "cct" from "centers_clients_maison"'
        )
        reference_dict = {
            item[0]: item[1] for item in query
        }
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
                raise ValueError(
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
    """Lancement script"""
    # ATTENTION! à Renommer aux besoins
    # =================================================================================
    nom_fichier_info = "Chronodirect_Septembre_2025.csv"
    date_facture = "20250930"
    # =================================================================================

    cnx_string = (
        "dbname=heron "
        "user=heron "
        "password=heron "
        "host=10.9.2.109 "
        "port=5439"
    )
    file_path = Path(rf"/Users/paulo/Downloads/{nom_fichier_info}")
    interne_file_path = Path(
        rf"/Users/paulo/Downloads/generique_interne_chronodirect_{date_facture}.csv"
    )
    set_generique_chrono_direct(cnx_string, file_path, interne_file_path, dte_fac=date_facture)
