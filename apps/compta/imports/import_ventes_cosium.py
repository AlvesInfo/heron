# pylint: disable=E0401,C0303
"""
FR : Module d'import du chiffre d'affaires Cosium (Ventes)
EN : Cosium turnover import module (Sales)

Commentaire:

created at: 2023-03-02
created by: Paulo ALVES

modified at: 2023-03-02
modified by: Paulo ALVES
"""
import pendulum
from psycopg2 import sql
from django.db import connection, transaction

from apps.core.functions.functions_setups import settings


HISTORIC_VENTES_ID = 24_673_943


def set_cct_ventes(cursor: connection.cursor):
    """Met à jour les cct dans les ventes
    :param cursor: cursor psycopg2
    :return:
    """
    sql_cct = sql.SQL(
        """
        update "compta_ventescosium" "cv" 
        set "cct_uuid_identification" = "cm"."cct_uuid_identification"
        from (
            select 
                "code_maison", 
                "cct", 
                "uuid_identification" as "cct_uuid_identification"
            from "centers_clients_maison" 
            where "code_maison" != '' and "code_maison" is not null
            union all 
            select 
                '703' as "code_maison", 
                'AF0705' as "cct", 
                '5a3819ab-4e67-4582-acd5-b5aa10e943ce'::uuid as "cct_uuid_identification"
        ) "cm"
        where "cv"."code_maison" = cm."code_maison"
        and "cv"."cct_uuid_identification" isnull
        """
    )
    cursor.execute(sql_cct)


@transaction.atomic
def insert_ventes_cosium():
    """Intégration des lignes de la table des ventes cosium
    :return:
    """

    with connection.cursor() as cursor:
        # ID Minimum pour le premier import
        sql_id = sql.SQL(
            """
            select 
                max("id_bi") as max_id
            from compta_ventescosium
            """
        )
        cursor.execute(sql_id)

        min_id = cursor.fetchone()[0] or HISTORIC_VENTES_ID
        print("intégration des lignes de ventes Cosium")
        sql_insert_ventes = sql.SQL(
            """
            insert into "compta_ventescosium" 
            (
                "id_bi", 
                "id_vente", 
                "code_ean", 
                "code_maison", 
                "code_cosium", 
                "famille_cosium", 
                "rayon_cosium", 
                "date_vente", 
                "qte_vente", 
                "remise", 
                "taux_tva", 
                "tva_x3", 
                "tva", 
                "total_ttc", 
                "pv_brut_unitaire", 
                "pv_net_unitaire", 
                "px_vente_ttc_devise", 
                "px_vente_ttc_devise_apres_remise", 
                "ca_ht_avt_remise", 
                "ca_ht_ap_remise", 
                "taux_change_bi", 
                "pv_brut_unitaire_eur_bi", 
                "pv_net_unitaire_eur_bi", 
                "px_vente_ttc_eur_bi", 
                "px_vente_ttc_eur_apres_remise_bi", 
                "ca_ht_avt_remise_eur_bi", 
                "ca_ht_ap_remise_eur_bi", 
                "px_achat_global", 
                "px_achat_unitaire", 
                "solde", 
                "maj_stock", 
                "age_client", 
                "centre_de_gestion", 
                "centre_payeur", 
                "code_barre_2", 
                "code_marketing_1", 
                "date_age_client", 
                "date_creation", 
                "date_encaissement", 
                "date_ordo", 
                "designation", 
                "filtre_pack", 
                "fournisseur", 
                "indentification_equip", 
                "indice", 
                "lentilles", 
                "marque", 
                "nom_mutuelle", 
                "num_client", 
                "num_devis_avoir", 
                "num_facture", 
                "pays", 
                "photochromique", 
                "prescripteur_na", 
                "prescripteurs",
                "sale_month"
            )
            select
                "id" as "id_bi", 
                "id_vente", 
                "code_ean", 
                "code_maison", 
                "code_cosium", 
                "famille_cosium", 
                "rayon_cosium", 
                "date_vente", 
                "qte_vente", 
                "remise", 
                "taux_tva", 
                "tva_x3", 
                "tva", 
                "total_ttc", 
                "pv_brut_unitaire", 
                "pv_net_unitaire", 
                "px_vente_ttc_devise", 
                "px_vente_ttc_devise_apres_remise", 
                "ca_ht_avt_remise", 
                "ca_ht_ap_remise", 
                "taux_change", 
                "pv_brut_unitaire_eur", 
                "pv_net_unitaire_eur", 
                "px_vente_ttc_eur", 
                "px_vente_ttc_eur_apres_remise", 
                "ca_ht_avt_remise_eur", 
                "ca_ht_ap_remise_eur", 
                "px_achat_global", 
                "px_achat_unitaire", 
                "solde", 
                "maj_stock", 
                "age_client", 
                "centre_de_gestion", 
                "centre_payeur", 
                "code_barre_2", 
                "code_marketing_1", 
                "date_age_client", 
                "date_creation", 
                "date_encaissement", 
                "date_ordo", 
                "designation", 
                "filtre_pack", 
                "fournisseur", 
                "indentification_equip", 
                "indice", 
                "lentilles", 
                "marque", 
                "nom_mutuelle", 
                "num_client", 
                "num_devis_avoir", 
                "num_facture", 
                "pays", 
                "photochromique", 
                "prescripteur_na", 
                "prescripteurs",
                date_trunc('month', "date_vente")::date as "sale_month"
            from "heron_bi_ventes_cosium"
            where "id" > %(min_id)s
            order by "id"
            """
        )
        cursor.execute(sql_insert_ventes, {"min_id": min_id})
        set_cct_ventes(cursor)

        # mise à jour du taux de change pour l'EURO
        sql_update_eur = """
        update "compta_ventescosium" "vc"
        set "taux_change_moyen" = "req"."rate",
            "ca_ht_ap_remise_eur" = "ca_ht_ap_remise",
            "ca_ht_avt_remise_eur" = "ca_ht_avt_remise",
            "pv_brut_unitaire_eur" = "pv_brut_unitaire",
            "pv_net_unitaire_eur" = "pv_net_unitaire",
            "px_vente_ttc_eur" = "px_vente_ttc_devise",
            "px_vente_ttc_eur_apres_remise" = "px_vente_ttc_devise_apres_remise"
        from (
            select 
                "cv"."id", "cc"."currency_iso", "pe"."rate_month", 1::numeric as "rate" 
            from "compta_ventescosium" "cv" 
            join "centers_clients_maison" "ccm" 
            on "cv"."cct_uuid_identification" = "ccm"."uuid_identification" 
            join "countries_country" "cc" 
            on "ccm"."pays" = "cc"."country" 
            join "parameters_exchangerate" "pe" 
            on "cv"."sale_month" = "pe"."rate_month"
            and "cc"."currency_iso" = "pe"."currency_change"
            and "pe"."currency_change" = 'EUR'
            and "cv"."taux_change_moyen" isnull
        ) req 
        where "vc"."id" = "req"."id"
        """
        cursor.execute(sql_update_eur)


@transaction.atomic
def mise_a_jour_ventes_cosium():
    """Mise à jour des lignes de la table des ventes cosium, en fin de mois ou lancement sur import
    défecteux sur la B.I
    :return:
    """

    with connection.cursor() as cursor:
        min_id = HISTORIC_VENTES_ID
        print("Mise à jour des lignes de ventes Cosium")
        sql_insert_ventes = sql.SQL(
            """
            insert into "compta_ventescosium" 
            (
                "id_bi", 
                "id_vente", 
                "code_ean", 
                "code_maison", 
                "code_cosium", 
                "famille_cosium", 
                "rayon_cosium", 
                "date_vente", 
                "qte_vente", 
                "remise", 
                "taux_tva", 
                "tva_x3", 
                "tva", 
                "total_ttc", 
                "pv_brut_unitaire", 
                "pv_net_unitaire", 
                "px_vente_ttc_devise", 
                "px_vente_ttc_devise_apres_remise", 
                "ca_ht_avt_remise", 
                "ca_ht_ap_remise", 
                "taux_change_bi", 
                "pv_brut_unitaire_eur_bi", 
                "pv_net_unitaire_eur_bi", 
                "px_vente_ttc_eu_bi", 
                "px_vente_ttc_eur_apres_remise_bi", 
                "ca_ht_avt_remise_eur_bi", 
                "ca_ht_ap_remise_eur_bi", 
                "px_achat_global", 
                "px_achat_unitaire", 
                "solde", 
                "maj_stock", 
                "age_client", 
                "centre_de_gestion", 
                "centre_payeur", 
                "code_barre_2", 
                "code_marketing_1", 
                "date_age_client", 
                "date_creation", 
                "date_encaissement", 
                "date_ordo", 
                "designation", 
                "filtre_pack", 
                "fournisseur", 
                "indentification_equip", 
                "indice", 
                "lentilles", 
                "marque", 
                "nom_mutuelle", 
                "num_client", 
                "num_devis_avoir", 
                "num_facture", 
                "pays", 
                "photochromique", 
                "prescripteur_na", 
                "prescripteurs",
                "sale_month"
            )
            select
                hbv."id" as "id_bi", 
                hbv."id_vente", 
                hbv."code_ean", 
                hbv."code_maison", 
                hbv."code_cosium", 
                hbv."famille_cosium", 
                hbv."rayon_cosium", 
                hbv."date_vente", 
                hbv."qte_vente", 
                hbv."remise", 
                hbv."taux_tva", 
                hbv."tva_x3", 
                hbv."tva", 
                hbv."total_ttc", 
                hbv."pv_brut_unitaire", 
                hbv."pv_net_unitaire", 
                hbv."px_vente_ttc_devise", 
                hbv."px_vente_ttc_devise_apres_remise", 
                hbv."ca_ht_avt_remise", 
                hbv."ca_ht_ap_remise", 
                hbv."taux_change", 
                hbv."pv_brut_unitaire_eur", 
                hbv."pv_net_unitaire_eur", 
                hbv."px_vente_ttc_eur", 
                hbv."px_vente_ttc_eur_apres_remise", 
                hbv."ca_ht_avt_remise_eur", 
                hbv."ca_ht_ap_remise_eur", 
                hbv."px_achat_global", 
                hbv."px_achat_unitaire", 
                hbv."solde", 
                hbv."maj_stock", 
                hbv."age_client", 
                hbv."centre_de_gestion", 
                hbv."centre_payeur", 
                hbv."code_barre_2", 
                hbv."code_marketing_1", 
                hbv."date_age_client", 
                hbv."date_creation", 
                hbv."date_encaissement", 
                hbv."date_ordo", 
                hbv."designation", 
                hbv."filtre_pack", 
                hbv."fournisseur", 
                hbv."indentification_equip", 
                hbv."indice", 
                hbv."lentilles", 
                hbv."marque", 
                hbv."nom_mutuelle", 
                hbv."num_client", 
                hbv."num_devis_avoir", 
                hbv."num_facture", 
                hbv."pays", 
                hbv."photochromique", 
                hbv."prescripteur_na", 
                hbv."prescripteurs",
                date_trunc('month', hbv."date_vente")::date as "sale_month"
            from "heron_bi_ventes_cosium" hbv
            where hbv."id" > %(min_id)s
            and not hbv."id" = any(
                (
                    select array_agg("id_bi") FROM (select "id_bi" from compta_ventescosium) cv
                )::INT[]
            )
            order by hbv."id"
            """
        )
        cursor.execute(sql_insert_ventes, {"min_id": min_id})
        set_cct_ventes(cursor)

        # mise à jour du taux de change pour l'EURO
        sql_update_eur = """
        update "compta_ventescosium" "vc"
        set "taux_change_moyen" = "req"."rate",
            "ca_ht_ap_remise_eur" = "ca_ht_ap_remise",
            "ca_ht_avt_remise_eur" = "ca_ht_avt_remise",
            "pv_brut_unitaire_eur" = "pv_brut_unitaire",
            "pv_net_unitaire_eur" = "pv_net_unitaire",
            "px_vente_ttc_eur" = "px_vente_ttc_devise",
            "px_vente_ttc_eur_apres_remise" = "px_vente_ttc_devise_apres_remise"
        from (
            select 
                "cv"."id", "cc"."currency_iso", "pe"."rate_month", 1::numeric as "rate" 
            from "compta_ventescosium" "cv" 
            join "centers_clients_maison" "ccm" 
            on "cv"."cct_uuid_identification" = "ccm"."uuid_identification" 
            join "countries_country" "cc" 
            on "ccm"."pays" = "cc"."country" 
            join "parameters_exchangerate" "pe" 
            on "cv"."sale_month" = "pe"."rate_month"
            and "cc"."currency_iso" = "pe"."currency_change"
            and "pe"."currency_change" = 'EUR'
            and "cv"."taux_change_moyen" isnull
        ) req 
        where "vc"."id" = "req"."id"
        """
        cursor.execute(sql_update_eur)


def force_update_sales(dte_d: str, dte_f: str):
    """Update Forcé des ventes par périodes"""
    date_debut = pendulum.parse(dte_d)
    date_fin = pendulum.parse(dte_f)

    with connection.cursor() as cursor:
        # Suppression des ventes de la période
        sql_delete_period = sql.SQL(
            """
            delete from compta_ventescosium
            where date_vente >= %(date_debut)s and date_vente <= %(date_fin)s
            """
        )
        cursor.execute(sql_delete_period, {"date_debut": date_debut, "date_fin": date_fin})

        # Insertion des ventes de la période
        sql_insert_ventes = sql.SQL(
            """
            insert into "compta_ventescosium" 
            (
                "id_bi", 
                "id_vente", 
                "code_ean", 
                "code_maison", 
                "code_cosium", 
                "famille_cosium", 
                "rayon_cosium", 
                "date_vente", 
                "qte_vente", 
                "remise", 
                "taux_tva", 
                "tva_x3", 
                "tva", 
                "total_ttc", 
                "pv_brut_unitaire", 
                "pv_net_unitaire", 
                "px_vente_ttc_devise", 
                "px_vente_ttc_devise_apres_remise", 
                "ca_ht_avt_remise", 
                "ca_ht_ap_remise", 
                "taux_change_bi", 
                "pv_brut_unitaire_eur_bi", 
                "pv_net_unitaire_eur_bi", 
                "px_vente_ttc_eur_bi", 
                "px_vente_ttc_eur_apres_remise_bi", 
                "ca_ht_avt_remise_eur_bi", 
                "ca_ht_ap_remise_eur_bi", 
                "px_achat_global", 
                "px_achat_unitaire", 
                "solde", 
                "maj_stock", 
                "age_client", 
                "centre_de_gestion", 
                "centre_payeur", 
                "code_barre_2", 
                "code_marketing_1", 
                "date_age_client", 
                "date_creation", 
                "date_encaissement", 
                "date_ordo", 
                "designation", 
                "filtre_pack", 
                "fournisseur", 
                "indentification_equip", 
                "indice", 
                "lentilles", 
                "marque", 
                "nom_mutuelle", 
                "num_client", 
                "num_devis_avoir", 
                "num_facture", 
                "pays", 
                "photochromique", 
                "prescripteur_na", 
                "prescripteurs",
                "sale_month"
            )
            select
                "id" as "id_bi", 
                "id_vente", 
                "code_ean", 
                "code_maison", 
                "code_cosium", 
                "famille_cosium", 
                "rayon_cosium", 
                "date_vente", 
                "qte_vente", 
                "remise", 
                "taux_tva", 
                "tva_x3", 
                "tva", 
                "total_ttc", 
                "pv_brut_unitaire", 
                "pv_net_unitaire", 
                "px_vente_ttc_devise", 
                "px_vente_ttc_devise_apres_remise", 
                "ca_ht_avt_remise", 
                "ca_ht_ap_remise", 
                "taux_change", 
                "pv_brut_unitaire_eur", 
                "pv_net_unitaire_eur", 
                "px_vente_ttc_eur", 
                "px_vente_ttc_eur_apres_remise", 
                "ca_ht_avt_remise_eur", 
                "ca_ht_ap_remise_eur", 
                "px_achat_global", 
                "px_achat_unitaire", 
                "solde", 
                "maj_stock", 
                "age_client", 
                "centre_de_gestion", 
                "centre_payeur", 
                "code_barre_2", 
                "code_marketing_1", 
                "date_age_client", 
                "date_creation", 
                "date_encaissement", 
                "date_ordo", 
                "designation", 
                "filtre_pack", 
                "fournisseur", 
                "indentification_equip", 
                "indice", 
                "lentilles", 
                "marque", 
                "nom_mutuelle", 
                "num_client", 
                "num_devis_avoir", 
                "num_facture", 
                "pays", 
                "photochromique", 
                "prescripteur_na", 
                "prescripteurs",
                date_trunc('month', "date_vente")::date as "sale_month"
            from "heron_bi_ventes_cosium"
            where date_vente >= %(date_debut)s and date_vente <= %(date_fin)s
            order by "id"
            """
        )
        cursor.execute(sql_insert_ventes, {"date_debut": date_debut, "date_fin": date_fin})

        # Mise à jour des cct des ventes sur la période
        sql_cct_update = sql.SQL(
            """
            update "compta_ventescosium" "cv" 
            set "cct_uuid_identification" = "cm"."cct_uuid_identification"
            from (
                select 
                    "code_maison", 
                    "cct", 
                    "uuid_identification" as "cct_uuid_identification"
                from "centers_clients_maison" 
                where "code_maison" != '' and "code_maison" is not null
                union all 
                select 
                    '703' as "code_maison", 
                    'AF0705' as "cct", 
                    '5a3819ab-4e67-4582-acd5-b5aa10e943ce'::uuid as "cct_uuid_identification"
            ) "cm"
            where "cv"."code_maison" = cm."code_maison"
            and "cv"."date_vente" >= %(date_debut)s and "cv"."date_vente" <= %(date_fin)s
            """
        )
        cursor.execute(sql_cct_update, {"date_debut": date_debut, "date_fin": date_fin})

        # mise à jour du taux de change pour l'EURO
        sql_update_eur = """
        update "compta_ventescosium" "vc"
        set "taux_change_moyen" = "req"."rate",
            "ca_ht_ap_remise_eur" = "ca_ht_ap_remise",
            "ca_ht_avt_remise_eur" = "ca_ht_avt_remise",
            "pv_brut_unitaire_eur" = "pv_brut_unitaire",
            "pv_net_unitaire_eur" = "pv_net_unitaire",
            "px_vente_ttc_eur" = "px_vente_ttc_devise",
            "px_vente_ttc_eur_apres_remise" = "px_vente_ttc_devise_apres_remise"
        from (
            select 
                "cv"."id", "cc"."currency_iso", "pe"."rate_month", 1::numeric as "rate" 
            from "compta_ventescosium" "cv" 
            join "centers_clients_maison" "ccm" 
            on "cv"."cct_uuid_identification" = "ccm"."uuid_identification" 
            join "countries_country" "cc" 
            on "ccm"."pays" = "cc"."country" 
            join "parameters_exchangerate" "pe" 
            on "cv"."sale_month" = "pe"."rate_month"
            and "cc"."currency_iso" = "pe"."currency_change"
            and "pe"."currency_change" = 'EUR'
            and "cv"."taux_change_moyen" isnull
        ) req 
        where "vc"."id" = "req"."id"
        """
        cursor.execute(sql_update_eur)


if __name__ == "__main__":
    # insert_ventes_cosium()
    # mise_a_jour_ventes_cosium()
    force_update_sales(dte_d="2023-04-01", dte_f="2023-04-30")
